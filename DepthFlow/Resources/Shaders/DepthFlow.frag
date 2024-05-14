/*
// (c) 2023-2024 CC BY-SA 4.0, Tremeschin
*/

void main() {
    Camera iCamera = iInitCamera(gluv);

    // Add parallax options
    iCamera.position.xy += iParallaxOffset;
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

    // Point where the ray intersects with the fixed image plane
    vec2 lambda = (iCamera.gluv - iCamera.position.xy);

    // Same as above but overshooted by depth focal point (fixed point at depth=focus)
    vec2 sigma  = iCamera.gluv - iCamera.position.xy * (1 + iParallaxFocus*iParallaxHeight);

    // The vector from Lambda to the camera's projection on the XY plane
    vec2 displacement = (iCamera.origin.xy - lambda) + iParallaxCenter;
    vec2 walk = normalize(displacement);

    // Angle between the Ray's origin and the XY plane
    float theta = atan(
        length(displacement),
        abs(1 - iCamera.origin.z)
    );

    // The distance Beta we care for the depth map
    float delta = abs(tan(theta) * (1 - iCamera.origin.z - iParallaxHeight));
    float alpha = abs(tan(theta) * (1 - iCamera.origin.z));
    float beta  = abs(alpha - delta);

    // Start the parallax on the point itself
    vec2 parallax = sigma;

    // The quality of the parallax effect is how tiny the steps are
    const float min_quality = 0.05;
    const float max_quality = 0.002;
    float quality = mix(min_quality, max_quality, iQuality);

    // Note: The Very Expensive Loop
    // Fixme: Can we smartly cache the last walk distance?
    // Fixme: Calculate walk distance based on pixel and angle?
    for (float i=1; i>0; i-=quality) {

        // Get the uv we'll check for the heights
        vec2 sample = sigma + (i*beta*walk);

        // Interpolate between (0=max) and (0=min) depending on focus
        float height       = gmtexture(depth, sample).r;
        float depth_height = iParallaxHeight * mix(height, 1-height, iParallaxInvert);
        float walk_height  = (i*beta) / tan(theta);

        // Stop whenever an intersection is found
        if (depth_height >= walk_height) {
            parallax = sample;
            break;
        }
    }

    // Draw the parallax image
    fragColor = gmtexture(image, parallax);
}

