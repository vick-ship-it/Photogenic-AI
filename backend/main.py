import os
import logging
from typing import Optional, Any, Dict

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

try:
    import replicate  # type: ignore
except Exception:  # pragma: no cover
    replicate = None  # Fallback if library isn't installed yet

from .prompt_builder import build_prompt


load_dotenv()

logger = logging.getLogger("photogenic-ai-studio")
logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    app = FastAPI(title="Photogenic AI Studio", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/api/generate")
    async def generate_image(
        reference_image: Optional[UploadFile] = File(default=None),
        gender: Optional[str] = Form(default=None),
        animal: Optional[str] = Form(default=None),
        expression: Optional[str] = Form(default=None),
        pose: Optional[str] = Form(default=None),
        outfit: Optional[str] = Form(default=None),
        lighting: Optional[str] = Form(default=None),
        camera: Optional[str] = Form(default=None),
        mood: Optional[str] = Form(default=None),
        background: Optional[str] = Form(default=None),
        seed: Optional[str] = Form(default=None),
    ) -> JSONResponse:
        """
        Generate a portrait using Replicate. If a reference image is provided and an
        image-to-image model is configured, use it; otherwise fall back to text-to-image.
        """
        fields = {
            "gender": gender,
            "animal": animal,
            "expression": expression,
            "pose": pose,
            "outfit": outfit,
            "lighting": lighting,
            "camera": camera,
            "mood": mood,
            "background": background,
        }
        positive_prompt, negative_prompt = build_prompt(fields)

        if replicate is None:
            raise HTTPException(status_code=500, detail="Replicate SDK is not installed. Run: pip install -r backend/requirements.txt")

        api_token = os.getenv("REPLICATE_API_TOKEN")
        if not api_token:
            raise HTTPException(status_code=400, detail="REPLICATE_API_TOKEN is not set. Provide it in your environment.")

        client = replicate.Client(api_token=api_token)

        text_model = os.getenv("REPLICATE_MODEL", "black-forest-labs/flux-1.1-pro")
        img2img_model = os.getenv("REPLICATE_IMAGE_TO_IMAGE_MODEL")

        # Build inputs conservatively to avoid model-specific parameter errors
        def _coerce_seed(raw: Optional[str]) -> Optional[int]:
            if not raw:
                return None
            try:
                return int(raw)
            except Exception:
                return None

        base_inputs: Dict[str, Any] = {"prompt": positive_prompt}
        # Note: Many models use different names for negative prompts; to remain
        # broadly compatible, we do not add it by default to inputs. The text of
        # negative prompt is embedded in the positive prompt context.
        maybe_seed = _coerce_seed(seed)
        if maybe_seed is not None:
            base_inputs["seed"] = maybe_seed

        try:
            if reference_image is not None and img2img_model:
                # Attempt image-to-image if configured.
                # Common parameter name is "image" for many models.
                inputs = dict(base_inputs)
                # Replicate Python SDK will upload file-like objects automatically.
                inputs["image"] = reference_image.file
                logger.info("Running Replicate image-to-image: %s", img2img_model)
                output = client.run(img2img_model, input=inputs)
            else:
                logger.info("Running Replicate text-to-image: %s", text_model)
                output = client.run(text_model, input=base_inputs)
        except Exception as e:  # pragma: no cover
            logger.exception("Replicate generation failed")
            raise HTTPException(status_code=502, detail=f"Generation failed: {e}")

        # Normalize output to a single image URL if possible
        image_url: Optional[str] = None
        if isinstance(output, list) and output:
            # Many models return a list of image URLs
            image_url = str(output[-1])
        elif isinstance(output, str):
            image_url = output
        elif isinstance(output, dict):
            # Some models return dicts; best effort
            image_url = str(output.get("image")) if output.get("image") else None

        if not image_url:
            raise HTTPException(status_code=500, detail="Model returned no image URL")

        return JSONResponse({"image_url": image_url, "prompt": positive_prompt})

    # Mount static frontend last so API routes take precedence
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()
