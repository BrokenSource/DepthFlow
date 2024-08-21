/*
// (c) 2023-2024 CC BY-SA 4.0, Tremeschin. Technically also AGPL-3.0
// but oh well, get in touch if you want to use it privately
*/

void main() {
    iCameraInit();

    // The distance the maximum depth projection plane is from the camera.
    float iDepthDistance = 1 + mix(0, iDepthHeight, iDepthFocus);

    // Add parallax options
    iCamera.position.xy += iDepthOffset;
    iCamera.isometric   += iDepthIsometric;
    iCamera.dolly       += iDepthDolly;
    iCamera.zoom        += (iDepthZoom - 1) + (iDepthDistance - 1);
    iCamera.plane_point  = vec3(0, 0, iDepthDistance);
    iCamera = iProjectCamera(iCamera);

    // Doesn't intersect with the XY plane
    if (iCamera.out_of_bounds) {
        fragColor = vec4(vec3(0.0), 1);
        return;
    }

    // Point where the ray intersects with the fixed image plane
    vec2 lambda = (iCamera.gluv - iCamera.position.xy) + iDepthCenter;

    // Same as above but overshoot by depth focal point (fixed offsets point at depth=focus)
    vec2 sigma = lambda - iCamera.position.xy * (iDepthStatic*iDepthHeight/iDepthDistance);

    // The vector from Lambda to the camera's projection on the XY plane
    vec2 displacement = (iCamera.origin.xy - lambda) + iDepthOrigin;
    vec2 walk = normalize(displacement);

    // Angle between the Ray's origin and the XY plane
    float theta = atan(
        length(displacement),
        abs(iDepthDistance - iCamera.origin.z)
    );

    // Cache tan(theta) and its inverse, we'll use it a lot
    float tan_theta = tan(theta);
    float tan_theta_inv = 1.0 / tan_theta;

    // The distance Beta we care for the depth map
    float delta = tan_theta * (iDepthDistance - iCamera.origin.z - iDepthHeight);
    float alpha = tan_theta * (iDepthDistance - iCamera.origin.z);
    float beta  = alpha - delta;

    // Start the parallax on the intersection point itself
    vec2 point_gluv = sigma;
    float point_height = 0;

    /* Main loop */ {

        // The quality of the parallax effect is how tiny the steps are
        float side = max(iResolution.x, iResolution.y);
        float quality = mix((side*0.05), (side*0.50), iQuality);

        // Optimization: Low quality first pass 'overshoot', high quality second pass 'backwards'
        float probe = mix(50, 100, iQuality);
        float i = 1;

        for (int stage=0; stage<2; stage++) {
            bool FORWARD  = (stage == 0);
            bool BACKWARD = (stage == 1);
            float di = (FORWARD ? (-1.0/probe) : (1.0/quality));

            while (true) {
                if (FORWARD && i < 0)
                    break;
                if (BACKWARD && 1 < i)
                    break;
                i += di;

                // The current point 'walks' on the util distance
                point_gluv   = sigma + (i*beta*walk);
                point_height = gtexture(depth, point_gluv, iDepthMirror).r;

                // Scale the values to intensity parameters
                float depth_height = iDepthHeight * mix(point_height, 1-point_height, iDepthInvert);
                float walk_height  = (i*beta) * tan_theta_inv;

                // Stop the first moment we're inside the surface
                if (depth_height >= walk_height) {
                    if (FORWARD) break;

                // Finish when we're outside at smaller steps
                } else if (BACKWARD) {
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

    if (iVigEnable) {
        vec2 away = astuv * (1 - astuv.yx);
        float linear = iVigIntensity * (away.x*away.y);
        fragColor.rgb *= clamp(pow(linear, iVigDecay), 0, 1);
    }

    // --------------------------------------------------------------------------------------------|
    // Colors post processing

    // Saturation
    float luminance = dot(fragColor.rgb, vec3(0.299, 0.587, 0.114));
    fragColor.rgb = mix(vec3(luminance), fragColor.rgb, iSaturation);
}
