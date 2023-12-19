from . import *


@attrs.define
class DepthFlowMDE:
    model: Any = None

    @property
    def cuda(self) -> bool:
        """Whether CUDA is available"""
        return torch.cuda.is_available()

    def load_model(self) -> None:
        """Load the model"""
        if self.model is None:
            self.model = torch.hub.load("isl-org/ZoeDepth", "ZoeD_N", pretrained=True)
            self.model.to("cuda" if self.cuda else "cpu")

    def __call__(self,
        image: Union[PilImage, PathLike, URL],
        normalized: bool=True,
        cache: bool=True,
    ) -> PilImage:
        """
        Estimate a Depth Map from an input image with a Monocular Depth Estimation model.

        Args:
            image:      The input image to estimate the depth map from, path, url, PIL
            normalized: Whether to normalize the depth map to (0, 1) based on the min and max values
            cache:      Whether to cache the depth map to the cache directory

        Returns:
            The estimated depth map as a PIL Image
        """

        # -----------------------------------------------------------------------------------------|
        # Caching

        # Load the image
        image = BrokenUtils.load_image(image)

        # Calculate hash of the image for caching
        image_hash = hashlib.md5(image.tobytes()).hexdigest()
        cache_path = DEPTHFLOW.DIRECTORIES.CACHE/f"{image_hash}.jpg"
        log.info(f"Image hash for Depth Map cache is [{image_hash}]")

        # If the depth map is cached, return it
        if cache and cache_path.exists():
            log.success(f"Depth map already cached on [{cache_path}]")
            return BrokenUtils.load_image(cache_path).convert("L")

        # -----------------------------------------------------------------------------------------|
        # Estimating

        self.load_model()

        # Estimate Depth Map
        with halo.Halo(text=f"Estimating Depth Map for the input image (CUDA: {self.cuda})"):
            depth_map = self.model.infer_pil(image)

        # -----------------------------------------------------------------------------------------|
        # Post-processing

        # Normalize the depth map to (0, 1) based on the min and max values
        if normalized and (factor := depth_map.max() - depth_map.min()) != 0:
            depth_map = 255 * (depth_map - depth_map.min()) / factor

        # Convert array to PIL Image RGB24
        depth_map = PIL.Image.fromarray(depth_map.astype(numpy.uint8))

        # -----------------------------------------------------------------------------------------|
        # Caching

        # Save image to Cache
        if cache:
            log.success(f"Saving depth map to cache path [{cache_path}]")
            depth_map.save(cache_path)

        return depth_map
