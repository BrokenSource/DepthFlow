/*
// (c) 2023-2024 CC BY-SA 4.0, Tremeschin
*/

void main() {
    Camera iCamera = iInitCamera(gluv);

    // The distance the maximum depth projection plane is from the camera.
    float iDepthDistance = 1 + mix(0, iDepthHeight, iDepthFocus);

    // Add parallax options
    iCamera.position.xy += iDepthOffset;
    iCamera.isometric   += iDepthIsometric;
    iCamera.dolly       += iDepthDolly;
    iCamera.zoom        += (iDepthZoom - 1) + (iDepthDistance - 1);
    iCamera.plane_point  = vec3(0, 0, iDepthDistance);
    iCamera              = iProjectCamera(iCamera);

    // Doesn't intersect with the XY plane
    if (iCamera.out_of_bounds) {
        fragColor = vec4(vec3(0.0), 1);
        return;
    }

    // // DepthFlow math

    // Point where the ray intersects with the fixed image plane
    vec2 lambda = (iCamera.gluv - iCamera.position.xy) + iDepthCenter;

    // Same as above but overshoot by depth focal point (fixed offsets point at depth=focus)
    vec2 sigma = iCamera.gluv - iCamera.position.xy * (1 + iDepthStatic*iDepthHeight/iDepthDistance) + iDepthCenter;

    // The vector from Lambda to the camera's projection on the XY plane
    vec2 displacement = (iCamera.origin.xy - lambda) + iDepthOrigin;
    vec2 walk = normalize(displacement);

    // Angle between the Ray's origin and the XY plane
    float theta = atan(
        length(displacement),
        abs(iDepthDistance - iCamera.origin.z)
    );

    // Cache tan(theta), we'll use it a lot
    float tan_theta = tan(theta);

    // The distance Beta we care for the depth map
    float delta = tan_theta * (iDepthDistance - iCamera.origin.z - iDepthHeight);
    float alpha = tan_theta * (iDepthDistance - iCamera.origin.z);
    float beta  = alpha - delta;

    // Start the parallax on the intersection point itself
    vec2 point_gluv = sigma;
    float point_height = 0;

    /* Main loop */ {

        // The quality of the parallax effect is how tiny the steps are
        // defined in pixels here. '* max_offset' without distortions
        float max_dimension = max(iResolution.x, iResolution.y);
        float max_quality = max_dimension * 0.50;
        float min_quality = max_dimension * 0.05;
        float quality = mix(min_quality, max_quality, iQuality);

        // Optimization: We'll do two swipes, one that is of lower quality (probe) just to find the
        // nearest intersection with the depth map, and then flip direction, at a finer (quality)
        float probe = mix(50, 100, iQuality);
        bool  swipe = true;
        float i = 1;

        for (int stage=0; stage<2; stage++) {
            bool FORWARD  = (stage == 0);
            bool BACKWARD = (stage == 1);

            while (swipe) {

                // Touched z=1 plane, no intersection
                if (FORWARD) {
                    if (i < 0) {
                        swipe = false;
                        break;
                    }

                // Out of bounds walking up
                } else if (1 < i) {
                    break;
                }

                // Integrate 'i', the ray parametric distance
                i -= FORWARD ? (1.0/probe) : (-1.0/quality);

                // Walk the util distance vector
                vec2 sample = sigma + (i*beta*walk);

                // Interpolate between (0=max) and (0=min) depending on focus
                float true_height  = gtexture(depth, sample, iDepthMirror).r;
                float depth_height = iDepthHeight * mix(true_height, 1-true_height, iDepthInvert);
                float walk_height  = (i*beta) / tan_theta;

                // Stop the first moment we're inside the surface
                if (depth_height >= walk_height) {
                    if (FORWARD) break;

                // Finish when we're outside at smaller steps
                } else if (BACKWARD) {
                    point_height = true_height;
                    point_gluv = sample;
                    break;
                }
            }
        }
    }

    // Start the color with the center point
    fragColor = gtexture(image, point_gluv, iDepthMirror);

    // --------------------------------------------------------------------------------------------|
    // Depth of Field

    if (iDofEnable) {
        float intensity = iDofIntensity * pow(smoothstep(iDofStart, iDofEnd, 1 - point_height), iDofExponent);
        vec4 color = fragColor;

        for (float angle=0; angle<TAU; angle+=TAU/iDofDirections) {
            for (float walk=1.0/iDofQuality; walk<=1.001; walk+=1.0/iDofQuality) {
                vec2 displacement = vec2(cos(angle), sin(angle)) * walk * intensity;
                color += gtexture(image, point_gluv + displacement, iDepthMirror);
            }
        }
        fragColor = color / (iDofDirections*iDofQuality);
    }

    // --------------------------------------------------------------------------------------------|
    // Vignette post processing

    if (iVignetteEnable) {
        vec2 away = astuv * (1 - astuv.yx);
        float linear = iVignetteIntensity * (away.x*away.y);
        fragColor.rgb *= clamp(pow(linear, iVignetteDecay), 0, 1);
    }
}

