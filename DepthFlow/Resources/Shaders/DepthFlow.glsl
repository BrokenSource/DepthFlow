/*
// (c) 2023-2024 CC BY-SA 4.0, Tremeschin. Technically also AGPL-3.0
// but oh well, get in touch if you want to use it privately
*/

/* ---------------------------------------------------------------------------------------------- */

struct DepthFlow {

    // Camera
    float isometric;
    float dolly;
    float zoom;
    vec3 plane;

    // Parallax
    float derivative;
    float steep;
    vec3 normal;
    vec2 offset;
    float height;
    float focus;
    vec2 center;
    float steady;
    vec2 origin;
    bool mirror;
    float invert;
    float quality;
    float away;

    // Output
    float value;
    vec2 gluv;
    bool oob;
};

DepthFlow DepthMake(
    Camera camera,
    DepthFlow depth,
    sampler2D depthmap
) {
    // The infinity projection plane's distance from the camera
    depth.away = 1.0 + mix(0.0, depth.height, depth.focus);

    // Inject parallax options on the camera
    camera.position.xy += depth.offset;
    camera.isometric   += depth.isometric;
    camera.dolly       += depth.dolly;
    camera.zoom        += (depth.zoom - 1.0) + ((1/depth.away) - 1.0);
    camera.plane_point  = vec3(0.0, 0.0, depth.away);
    camera              = iCameraProject(camera);
    depth.oob           = camera.out_of_bounds;

    if (depth.oob)
        return depth;

    // Point where the ray intersects with the infinity plane, with a fixed point
    // pivoting around depth=steady. I do not know how the math works.
    vec2 intersect = (depth.center + camera.gluv)
        - camera.position.xy * (1 + depth.steady * depth.height / depth.away);

    depth.gluv = intersect;

    // The direction to converge to the ray's origin from the intersection
    vec2 displacement = (camera.origin.xy - intersect) + depth.origin;
    vec2 walk = normalize(displacement);

    // Angle between the ray vector and the XY plane
    float tan_theta = length(displacement) / abs(depth.away - camera.origin.z);
    float cot_theta = (1.0/tan_theta);

    // Note: Edge case on parallel rays
    if (abs(tan_theta) < 1e-6)
        return depth;

    // The util distance the 'projection ceiling' is always above the surface
    float edge = tan_theta * (depth.away - camera.origin.z - depth.height);
    float util = (length(displacement) - edge);

    // The quality of the parallax effect is how tiny the steps are
    float side = max(iResolution.x, iResolution.y);
    float quality = 1.0 / mix((side*0.05), (side*0.50), depth.quality);

    // Optimization: Low quality overshoot, high quality reverse
    float probe = (-1.0) / mix(50.0, 100.0, depth.quality);
    float i = 1.0;

    // Utilities
    float last_value = 0.0;

    /* Main loop: Find the intersection with the scene */
    for (int stage=0; stage<2; stage++) {
        bool FORWARD  = (stage == 0);
        bool BACKWARD = (stage == 1);

        while (true) {
            if (FORWARD && i < 0.0)
                break;
            if (BACKWARD && 1.0 < i)
                break;

            i += (FORWARD ? probe : quality);

            // The checking point 'walks' on the util distance
            last_value  = depth.value;
            depth.gluv  = intersect + (i*util*walk);
            depth.value = gtexture(depthmap, depth.gluv, depth.mirror).r;

            // Fixme optimization (+8%): Avoid recalculating 'invert'
            float surface = depth.height * mix(depth.value, 1.0-depth.value, depth.invert);
            float ceiling = cot_theta * (i*util);

            // Stop the first moment we're inside the surface
            if (surface >= ceiling) {
                if (FORWARD) break;

            // Finish when we're outside at smaller steps
            } else if (BACKWARD) {
                depth.derivative = (last_value - depth.value) / quality;
                break;
            }
        }
    }

    // The gradient is always normal to a surface; assume the change
    // of z is proportional to the maximum surface height
    depth.normal = normalize(vec3(
        (gtexture(depthmap, depth.gluv - vec2(quality, 0), depth.mirror).r - depth.value) / quality,
        (gtexture(depthmap, depth.gluv - vec2(0, quality), depth.mirror).r - depth.value) / quality,
        max(depth.height, quality)
    ));

    // Heuristic to determine the perceptual steepness of the surface, 'gaps'
    depth.steep = depth.derivative * angle(depth.normal, vec3(0, 0, 1));

    return depth;
}

/* ---------------------------------------------------------------------------------------------- */

DepthFlow depthflow;

void iDepthInit() {
    depthflow.isometric = iDepthIsometric;
    depthflow.dolly     = iDepthDolly;
    depthflow.zoom      = iDepthZoom;
    depthflow.offset    = iDepthOffset;
    depthflow.height    = iDepthHeight;
    depthflow.focus     = iDepthFocus;
    depthflow.center    = iDepthCenter;
    depthflow.steady    = iDepthSteady;
    depthflow.origin    = iDepthOrigin;
    depthflow.mirror    = iDepthMirror;
    depthflow.invert    = iDepthInvert;
    depthflow.quality   = iQuality;
    depthflow.away      = 1.0;
    depthflow.value     = 0.0;
    depthflow.gluv      = vec2(0.0);
    depthflow.oob       = false;
}

/* ---------------------------------------------------------------------------------------------- */

void main() {
    iCameraInit();
    iDepthInit();
    depthflow = DepthMake(iCamera, depthflow, depth);
    fragColor = gtexture(image, depthflow.gluv, depthflow.mirror);

    if (depthflow.oob) {
        fragColor = vec4(vec3(0.0), 1);
        return;
    }

    /* --------------------------------------- */

    // Inpaint masking
    if (iInpaint && depthflow.steep > iInpaintLimit) {
        fragColor = vec4(0, 1, 0, 1);
        return;
    } else if (iInpaintBlack) {
        fragColor = vec4(0, 0, 0, 1);
        return;
    }

    // Fixme: Ability to apply lens and blur on multi-pass (post-refactor and metaprograming overhaul)

    // Lens distortion (Mutually exclusive with blur)
    if (iLensEnable) {

        // Define the base 'velocity' (intensity) of the effect
        float decay = pow(0.62*length(agluv), (10 - 9*iLensDecay));
        vec2 delta = (0.5*iLensIntensity) * normalize(agluv) * decay;
        vec3 color = vec3(0);

        // Integrate the color along the path, different speeds per channel
        for (float i=0; i<1; i+=(1.0/iLensQuality)) {
            color.r += gtexture(image, depthflow.gluv - (1*i*delta), depthflow.mirror).r;
            color.g += gtexture(image, depthflow.gluv - (2*i*delta), depthflow.mirror).g;
            color.b += gtexture(image, depthflow.gluv - (4*i*delta), depthflow.mirror).b;
        }

        // Normalize the color, as it grew with integration
        fragColor.rgb = (color / iLensQuality);
    }

    // Depth of Field (Mutually exclusive with lens distortion)
    else if (iBlurEnable) {
        float intensity = iBlurIntensity * pow(smoothstep(iBlurStart, iBlurEnd, 1.0 - depthflow.value), iBlurExponent);
        vec4 color = fragColor;

        for (float angle=0.0; angle<TAU; angle+=TAU/iBlurDirections) {
            for (float walk=1.0/iBlurQuality; walk<=1.001; walk+=1.0/iBlurQuality) {
                vec2 displacement = vec2(cos(angle), sin(angle)) * walk * intensity;
                color += gtexture(image, depthflow.gluv + displacement, depthflow.mirror);
            }
        }
        fragColor = color / (iBlurDirections*iBlurQuality);
    }

    // Vignette post processing
    if (iVigEnable) {
        vec2 away = astuv * (1.0 - astuv.yx);
        float linear = iVigIntensity * (away.x*away.y);
        fragColor.rgb *= clamp(pow(linear, iVigDecay), 0.0, 1.0);
    }

    // Colors post processing
    float luminance;

    // Saturation
    luminance     = dot(fragColor.rgb, vec3(0.299, 0.587, 0.114));
    fragColor.rgb = mix(vec3(luminance), fragColor.rgb, iColorsSaturation);

    // Contrast
    fragColor.rgb = mix(vec3(0.5), fragColor.rgb, iColorsContrast);

    // Brightness
    fragColor.rgb += (iColorsBrightness - 1);

    // Gamma
    fragColor.rgb = pow(fragColor.rgb, vec3(1.0/iColorsGamma));

    // Sepia
    luminance     = dot(fragColor.rgb, vec3(0.299, 0.587, 0.114));
    fragColor.rgb = mix(fragColor.rgb, luminance*vec3(1.2, 1.0, 0.8), iColorsSepia);

    // Grayscale
    luminance     = dot(fragColor.rgb, vec3(0.299, 0.587, 0.114));
    fragColor.rgb = mix(fragColor.rgb, vec3(luminance), iColorsGrayscale);
}
