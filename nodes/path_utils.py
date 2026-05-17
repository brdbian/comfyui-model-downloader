import os


def suggest_local_path(filename: str, model_dirs: list[str]) -> str:
    normalized = filename.replace("\\", "/").lower()
    hints = (
        ("text_encoders", "text_encoders"),
        ("diffusion_models", "diffusion_models"),
        ("/unet/", "diffusion_models"),
        ("/vae/", "vae"),
        ("/clip/", "clip"),
        ("/loras/", "loras"),
        ("/lora/", "loras"),
    )
    for pattern, folder in hints:
        if pattern in normalized and folder in model_dirs:
            return folder

    _, ext = os.path.splitext(os.path.basename(filename))
    if ext in (".ckpt", ".safetensors", ".pt", ".pth", ".bin"):
        for folder in ("checkpoints", "diffusion_models", "unet"):
            if folder in model_dirs:
                return folder

    return model_dirs[0] if model_dirs else "checkpoints"


def resolve_save_target(
    repo_filename: str,
    local_path: str,
    model_dirs: list[str],
    local_path_override: str = "",
) -> tuple[str, str]:
    if local_path_override:
        final_path = local_path_override
        flatten = True
    elif local_path == "Auto":
        final_path = suggest_local_path(repo_filename, model_dirs)
        flatten = True
    else:
        final_path = local_path
        flatten = False

    save_filename = os.path.basename(repo_filename) if flatten else repo_filename
    return final_path, save_filename
