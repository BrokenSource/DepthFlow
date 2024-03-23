/*
// (c) 2023-2024 CC BY-SA 4.0, Tremeschin
*/

void main() {
    Camera iCamera = iInitCamera(gluv);

    // Add parallax options
    iCamera.position.xy += iParallaxPosition;
    iCamera.isometric   += iParallaxIsometric;
    iCamera.dolly       += iParallaxDolly;
    iCamera.zoom        += iParallaxZoom - 1;
    iCamera              = iProjectCamera(iCamera);

    // Doesn't intersect with the XY plane
    if (iCamera.out_of_bounds) {
        fragColor = vec4(vec3(0.2), 1);
        return;
    }

    // // DepthFlow math

    // Point where the ray intersects with the XY plane
    vec2 lambda = iCamera.gluv;

    // No camera displacement mode, raw parallax
    if (iParallaxFixed) {
        lambda -= iCamera.position.xy;
    }

    // The vector from Lambda to the camera's projection on the XY plane
    vec2 displacement = iCamera.origin.xy - lambda;

    // Angle between the Ray's origin and the XY plane
    float theta = atan(
        length(displacement),
        abs(1 - iCamera.origin.z)
    );

    // The distance Beta we care for the depth map
    float delta = abs(tan(theta) * (1 - iCamera.origin.z - iParallaxHeight));
    float alpha = abs(tan(theta) * (1 - iCamera.origin.z));
    float beta  = abs(alpha - delta);

    // The vector we should walk towards
    vec2 walk = normalize(displacement);

    // Start the parallax on the point itself
    vec2 parallax = lambda;

    // The quality of the parallax effect is how tiny the steps are
    const float min_quality = 0.07;
    const float max_quality = 0.002;
    float quality = mix(min_quality, max_quality, iQuality);

    // Fixme: Can we smartly cache the last walk distance?
    // Fixme: Calculate walk distance based on pixel and angle?
    // The Very Expensive Loop™
    for (float i=0.0; i<1.0; i+=quality) {

        // Get the uv we'll check for the heights
        vec2 sample = gluv2stuv(lambda + i*beta*walk);

        // The depth map value
        float depth_height = iParallaxHeight * draw_image(depth, sample).r;
        float walk_height  = (i*beta) / tan(theta);

        // Update uv until the last height > walk
        if (depth_height >= walk_height) {
            parallax = sample;
        }
    }

    // Draw the parallax image
    fragColor = draw_image(image, parallax);
}

