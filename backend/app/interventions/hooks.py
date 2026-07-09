from __future__ import annotations
import logging
import torch
from .vector_lookup import get_lens_vector, check_intervention_supported
from .schemas import InterventionConfig

logger = logging.getLogger(__name__)

EPS = 1e-8


class InterventionContext:
    def __init__(self, loaded_model, lens, tokenizer, intervention: InterventionConfig):
        self.loaded_model = loaded_model
        self.lens = lens
        self.tokenizer = tokenizer
        self.intervention = intervention
        self.handles = []
        self.vector = None

    def __enter__(self):
        if not self.intervention.enabled or self.intervention.mode == "none":
            return self
        cfg = self.intervention
        try:
            if cfg.mode == "add":
                token_text = cfg.token
                if not token_text:
                    raise ValueError("add mode requires a token")
                self.vector = get_lens_vector(None, self.lens, self.tokenizer, token_text, cfg.layer_start or 0)
            elif cfg.mode == "ablate":
                token_text = cfg.token
                if not token_text:
                    raise ValueError("ablate mode requires a token")
                self.vector = get_lens_vector(None, self.lens, self.tokenizer, token_text, cfg.layer_start or 0)
            elif cfg.mode == "swap":
                if not cfg.source_token:
                    raise ValueError("swap mode requires source_token")
                if not cfg.target_token:
                    raise ValueError("swap mode requires target_token")
                self.source_vector = get_lens_vector(None, self.lens, self.tokenizer, cfg.source_token, cfg.layer_start or 0)
                self.target_vector = get_lens_vector(None, self.lens, self.tokenizer, cfg.target_token, cfg.layer_start or 0)
        except Exception as e:
            logger.error("Vector lookup failed for intervention mode=%s: %s", cfg.mode, e)
            raise

        if self.vector is not None and cfg.normalize_vector:
            self.vector = self.vector / (self.vector.norm() + EPS)
        if hasattr(self, "source_vector") and self.source_vector is not None and cfg.normalize_vector:
            self.source_vector = self.source_vector / (self.source_vector.norm() + EPS)
        if hasattr(self, "target_vector") and self.target_vector is not None and cfg.normalize_vector:
            self.target_vector = self.target_vector / (self.target_vector.norm() + EPS)

        hook = self._make_hook(cfg)
        target_layers = self._get_target_layers(cfg)
        for layer_idx in target_layers:
            module = self._get_layer_module(self.loaded_model, layer_idx)
            if module is not None:
                handle = module.register_forward_hook(hook)
                self.handles.append(handle)
                logger.info("Registered intervention hook on layer %d", layer_idx)

        return self

    def __exit__(self, exc_type, exc, tb):
        for h in self.handles:
            try:
                h.remove()
            except Exception as e:
                logger.warning("Failed to remove hook: %s", e)
        self.handles.clear()
        logger.info("Removed %d intervention hooks", len(self.handles))

    def _get_target_layers(self, cfg: InterventionConfig) -> list[int]:
        max_layer = 32
        if hasattr(self.lens, "W_U") and isinstance(self.lens.W_U, torch.Tensor):
            max_layer = self.lens.W_U.shape[0]
        elif hasattr(self.lens, "W_U") and isinstance(self.lens.W_U, dict):
            max_layer = max(self.lens.W_U.keys()) + 1
        start = cfg.layer_start if cfg.layer_start is not None else 0
        end = cfg.layer_end if cfg.layer_end is not None else max_layer
        return list(range(start, min(end, max_layer), cfg.layer_step))

    def _get_layer_module(self, model, layer_idx: int):
        if hasattr(model, "model") and hasattr(model.model, "layers"):
            layers = model.model.layers
            if 0 <= layer_idx < len(layers):
                return layers[layer_idx]
        if hasattr(model, "transformer") and hasattr(model.transformer, "h"):
            layers = model.transformer.h
            if 0 <= layer_idx < len(layers):
                return layers[layer_idx]
        if hasattr(model, "gpt_neox") and hasattr(model.gpt_neox, "layers"):
            layers = model.gpt_neox.layers
            if 0 <= layer_idx < len(layers):
                return layers[layer_idx]
        if hasattr(model, "model") and hasattr(model.model, "decoder") and hasattr(model.model.decoder, "layers"):
            layers = model.model.decoder.layers
            if 0 <= layer_idx < len(layers):
                return layers[layer_idx]
        logger.warning("Could not find layer module at index %d for model type %s", layer_idx, type(model).__name__)
        return None

    def _make_hook(self, cfg: InterventionConfig):
        vec = self.vector
        src_vec = getattr(self, "source_vector", None)
        tgt_vec = getattr(self, "target_vector", None)

        def hook_fn(module, input_tensors, output):
            nonlocal vec, src_vec, tgt_vec
            hidden = output[0] if isinstance(output, tuple) else output
            positions = self._get_positions(hidden, cfg)

            if cfg.mode == "add" and vec is not None:
                alpha = cfg.alpha
                for p in positions:
                    hidden[:, p, :] = hidden[:, p, :] + alpha * vec.to(hidden.device, hidden.dtype)

            elif cfg.mode == "ablate" and vec is not None:
                alpha = cfg.alpha
                vec_device = vec.to(hidden.device, hidden.dtype)
                vec_unit = vec_device / (vec_device.norm() + EPS)
                for p in positions:
                    h = hidden[:, p, :]
                    proj = torch.dot(h.squeeze(), vec_unit.squeeze()) * vec_unit
                    hidden[:, p, :] = hidden[:, p, :] - alpha * proj

            elif cfg.mode == "swap" and src_vec is not None and tgt_vec is not None:
                alpha = cfg.alpha
                src = src_vec.to(hidden.device, hidden.dtype)
                src_unit = src / (src.norm() + EPS)
                tgt = tgt_vec.to(hidden.device, hidden.dtype)
                tgt_unit = tgt / (tgt.norm() + EPS)
                for p in positions:
                    h = hidden[:, p, :]
                    proj_strength = torch.dot(h.squeeze(), src_unit.squeeze())
                    source_proj = proj_strength * src_unit
                    hidden[:, p, :] = hidden[:, p, :] - source_proj + alpha * proj_strength * tgt_unit

            if isinstance(output, tuple):
                return (hidden,) + output[1:]
            return hidden

        return hook_fn

    def _get_positions(self, hidden: torch.Tensor, cfg: InterventionConfig):
        seq_len = hidden.shape[1]
        if cfg.position_mode == "all":
            return list(range(seq_len))
        elif cfg.position_mode == "last_prompt":
            return [seq_len - 1]
        elif cfg.position_mode == "selected" and cfg.selected_positions:
            return [p for p in cfg.selected_positions if 0 <= p < seq_len]
        elif cfg.position_mode == "generated_only":
            return list(range(seq_len))
        return list(range(seq_len))
