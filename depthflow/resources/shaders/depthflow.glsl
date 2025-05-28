/*
// (c) 2023-2025 CC BY-SA 4.0, Tremeschin. Technically also AGPL-3.0,
// but oh well, get in touch if you want to use it privately
*/

/* ---------------------------------------------------------------------------------------------- */

#ifndef DEPTHFLOW
#define DEPTHFLOW

struct DepthFlow {
    float quality;
    float height;
    float steady;
    float focus;
    float zoom;
    float isometric;
    float dolly;
    float invert;
    bool mirror;
    vec2 offset;
    vec2 center;
    vec2 origin;
    bool glued;
    // Output
    float derivative;
    float steep;
    float value;
    vec3 normal;
    vec2 gluv;
    bool oob;
};

DepthFlow DepthMake(
    Camera camera,
    DepthFlow depth,
    sampler2D depthmap
) {
    // Convert absolute values to relative values
    float rel_focus  = (depth.focus  * depth.height);
    float rel_steady = (depth.steady * depth.height);

    // Inject parallax options on the camera
    camera.position.xy += depth.offset;
    camera.isometric   += depth.isometric;
    camera.dolly       += depth.dolly;
    camera.zoom        += (depth.zoom - 1.0);
    camera.focal_length = (1.0 - rel_focus);
    camera.plane_point  = vec3(0.0, 0.0, 1.0);
    camera              = CameraProject(camera);
    depth.oob           = camera.out_of_bounds;

    if (depth.oob)
        return depth;

    // Shift ray origin to the target center point
    camera.origin += vec3(depth.origin, 0);

    // Point where the ray intersects with a fixed point pivoting around depth=steady
    vec3 intersect = vec3(depth.center + camera.gluv, 1.0)
        - vec3(camera.position.xy, 0.0) * (1.0/(1.0 - rel_steady)) * int(depth.glued);

    // The quality of the parallax effect is how tiny the steps are
    // Optimization: Low quality overshoot, high quality reverse
    float quality = (1.0 / mix(200, 2000, depth.quality));
    float probe   = (1.0 / mix( 50,  120, depth.quality));

    // The guaranteed relative distance to not hit the surface
    float safe = (1.0 - depth.height);
    float last_value = 0.0;
    float walk = 0.0;

    /* Main loop: Find the intersection with the scene */
    for (int stage=0; stage<2; stage++) {
        bool FORWARD  = (stage == 0);
        bool BACKWARD = (stage == 1);

        // Safety max iterations
        for (int it=0; it<1000; it++) {
            if (FORWARD && walk > 1.0)
                break;

            walk += (FORWARD ? probe : -quality);

            // Interpolate origin and intersect, starting at minimum safe distance
            vec3 point = mix(camera.origin, intersect, mix(safe, 1.0, walk));
            depth.gluv = point.xy;

            // Sample next depth value
            last_value = depth.value;
            depth.value = gtexture(depthmap, depth.gluv, depth.mirror).r;

            // Fixme optimization (+8%): Avoid recalculating 'invert'
            float surface = depth.height * mix(depth.value, 1.0 - depth.value, depth.invert);
            float ceiling = (1.0 - point.z);

            // Stop the first moment we're inside the surface
            if (ceiling < surface) {
                if (FORWARD) break;

            // Finish when outside at smaller steps
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

#define GetDepthFlow(name) \
    DepthFlow name; \
    { \
        name.isometric = name##Isometric; \
        name.dolly     = name##Dolly; \
        name.zoom      = name##Zoom; \
        name.offset    = name##Offset; \
        name.height    = name##Height; \
        name.focus     = name##Focus; \
        name.center    = name##Center; \
        name.steady    = name##Steady; \
        name.origin    = name##Origin; \
        name.mirror    = name##Mirror; \
        name.invert    = name##Invert; \
        name.quality   = iQuality; \
        name.glued     = true; \
        name.value     = 0.0; \
        name.gluv      = vec2(0.0); \
        name.oob       = false; \
    }
#endif

/* ---------------------------------------------------------------------------------------------- */


void main() {
    GetCamera(iCamera);
    GetDepthFlow(iDepth);
    DepthFlow depthflow = DepthMake(iCamera, iDepth, depth);
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
        float linear = iVigDecay * (away.x*away.y);
        fragColor.rgb *= clamp(pow(linear, iVigIntensity), 0.0, 1.0);
    }

    // Colors post processing
    float luminance;

    /* Saturation */ if (iColorsSaturation != 1.0) {
        vec3 _hsv = rgb2hsv(fragColor.rgb);
        _hsv.y = clamp(_hsv.y * iColorsSaturation, 0.0, 1.0);
        fragColor.rgb = hsv2rgb(_hsv);
    }

    /* Contrast */ if (iColorsContrast != 1.0) {
        fragColor.rgb = clamp((fragColor.rgb - 0.5) * iColorsContrast + 0.5, 0.0, 1.0);
    }

    /* Brightness */ if (iColorsBrightness != 1.0) {
        fragColor.rgb = clamp(fragColor.rgb * iColorsBrightness, 0.0, 1.0);
    }

    /* Gamma */ if (iColorsGamma != 1.0) {
        fragColor.rgb = pow(fragColor.rgb, vec3(1.0/iColorsGamma));
    }

    /* Sepia */ if (iColorsSepia != 0.0) {
        luminance     = dot(fragColor.rgb, vec3(0.299, 0.587, 0.114));
        fragColor.rgb = mix(fragColor.rgb, luminance*vec3(1.2, 1.0, 0.8), iColorsSepia);
    }

    /* Grayscale */ if (iColorsGrayscale != 0.0) {
        luminance     = dot(fragColor.rgb, vec3(0.299, 0.587, 0.114));
        fragColor.rgb = mix(fragColor.rgb, vec3(luminance), iColorsGrayscale);
    }
}
