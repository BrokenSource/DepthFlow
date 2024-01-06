
void main() {
    SombreroCamera iCamera = iInitSombreroCamera(gluv);

    // Add parallax options
    iCamera.position.yz += iParallaxPosition;
    iCamera.isometric = iParallaxIsometric;

    // Project camera Rays
    iCamera = iProjectSombreroCamera(iCamera);

    // Doesn't intersect with the YZ plane
    if (iCamera.out_of_bounds) {
        fragColor.rgb = vec3(0.2);
        return;
    }

    // Apply and fix camera Zoom due isometric
    iCamera.uv *= iParallaxZoom;
    iCamera.uv *= 1 - pow(iParallaxHeight*iParallaxIsometric, 2);

    // // DepthFlow math

    // Point where the ray intersects with the YZ plane
    vec2 lambda = iCamera.uv;

    // No camera displacement mode, raw parallax
    if (iParallaxFixed) {
        lambda -= vec2(-iCamera.position.y, iCamera.position.z);
    }

    // The vector from Lambda to the camera's projection on the YZ plane
    vec2 displacement = vec2(-iCamera.origin.y, iCamera.origin.z) - lambda;

    // Angle between the Ray's origin and the YZ plane
    float theta = atan(
        length(displacement),
        abs(1 - iCameraPosition.x)
    );

    // The distance Beta we care for the depth map
    float delta = abs(tan(theta) * (1 - iCamera.origin.x - iParallaxHeight));
    float alpha = abs(tan(theta) * (1 - iCamera.origin.x));
    float beta  = abs(alpha - delta);

    // The vector we should walk towards
    vec2 walk = normalize(displacement);

    // Start the parallax on the point itself
    vec2 parallax = lambda;

    // The quality of the parallax effect is how tiny the steps are
    float quality;
    switch (iQuality) {
        case 0: quality = 0.05;  break;
        case 1: quality = 0.02;  break;
        case 2: quality = 0.01; break;
        case 3: quality = 0.008; break;
        case 4: quality = 0.003; break;
    }

    // Fixme: Can we smartly cache the last walk distance?
    // Fixme: Calculate walk distance based on pixel and angle?
    // The Very Expensive Loop™
    for (float i=0.0; i<1.0; i+=quality) {

        // Get the uv we'll check for the heights
        vec2 sample = gluv2stuv(lambda + i*beta*walk);

        // The depth map value
        float depth_height = iParallaxHeight * (1.0 - draw_image(depth, sample).r);
        float walk_height  = (i*beta) / tan(theta);

        // Update uv until the last height > walk
        if (depth_height >= walk_height) {
            parallax = sample;
        }
    }

    // Draw the parallax image
    fragColor = draw_image(image, parallax);
}

