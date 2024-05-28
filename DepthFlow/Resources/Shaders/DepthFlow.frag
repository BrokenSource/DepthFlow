/*
// (c) 2023-2024 CC BY-SA 4.0, Tremeschin
*/

void main() {
    Camera iCamera = iInitCamera(gluv);

    // The distance the maximum depth projection plane is from the camera.
    float iParallaxDistance = 1 + mix(0, iParallaxHeight, iParallaxPlane);

    // Add parallax options
    iCamera.position.xy += iParallaxOffset;
    iCamera.isometric   += iParallaxIsometric;
    iCamera.dolly       += iParallaxDolly;
    iCamera.zoom        += (iParallaxZoom - 1) + (iParallaxDistance - 1);
    iCamera.plane_point  = vec3(0, 0, iParallaxDistance);
    iCamera              = iProjectCamera(iCamera);

    // Doesn't intersect with the XY plane
    if (iCamera.out_of_bounds) {
        fragColor = vec4(vec3(0.2), 1);
        return;
    }

    // // DepthFlow math

    // Point where the ray intersects with the fixed image plane
    vec2 lambda = (iCamera.gluv - iCamera.position.xy);

    // Same as above but overshoot by depth focal point (fixed offsets point at depth=focus)
    vec2 sigma  = iCamera.gluv - iCamera.position.xy * (1 + iParallaxFocus*iParallaxHeight/iParallaxDistance);

    // The vector from Lambda to the camera's projection on the XY plane
    vec2 displacement = (iCamera.origin.xy - lambda) + iParallaxCenter;
    vec2 walk = normalize(displacement);

    // Angle between the Ray's origin and the XY plane
    float theta = atan(
        length(displacement),
        abs(iParallaxDistance - iCamera.origin.z)
    );

    // The distance Beta we care for the depth map
    float delta = tan(theta) * (iParallaxDistance - iCamera.origin.z - iParallaxHeight);
    float alpha = tan(theta) * (iParallaxDistance - iCamera.origin.z);
    float beta  = alpha - delta;

    // Start the parallax on the intersection point itself
    vec2 point_gluv = sigma;
    float point_height = 0;

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
        float true_height  = gtexture(depth, sample, iParallaxMirror).r;
        float depth_height = iParallaxHeight * mix(true_height, 1-true_height, iParallaxInvert);
        float walk_height  = (i*beta) / tan(theta);

        // Stop whenever an intersection is found
        if (depth_height >= walk_height) {
            point_height = true_height;
            point_gluv = sample;
            break;
        }
    }

    // Start the color with the center point
    fragColor = gtexture(image, point_gluv, iParallaxMirror);

    // Depth of Field (A bit expensive of a blur)
    if (iDofEnable) {
        float intensity = iDofIntensity * pow(smoothstep(iDofStart, iDofEnd, 1 - point_height), iDofExponent);
        vec4 color = fragColor;

        for (float angle=0; angle<TAU; angle+=TAU/iDofDirections) {
            for (float walk=1.0/iDofQuality; walk<=1.001; walk+=1.0/iDofQuality) {
                vec2 displacement = vec2(cos(angle), sin(angle)) * walk * intensity;
                color += gtexture(image, point_gluv + displacement, iParallaxMirror);
            }
        }
        fragColor = color / (iDofDirections*iDofQuality);
    }

    // Vignette post processing
    if (iVignetteEnable) {
        vec2 away = astuv * (1 - astuv.yx);
        float linear = iVignetteIntensity * (away.x*away.y);
        fragColor.rgb *= clamp(pow(linear, iVignetteDecay), 0, 1);
    }
}

