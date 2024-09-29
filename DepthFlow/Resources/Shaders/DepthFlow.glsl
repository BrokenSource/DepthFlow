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
    bool oob;

    // Parallax
    float quality;
    float invert;
    float height;
    float steady;
    float focus;
    float away;
    vec2 offset;
    vec2 center;
    vec2 origin;
    bool mirror;

    // Output
    float value;
    vec2 gluv;
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

    if (camera.out_of_bounds) {
        depth.oob = true;
        return depth;
    }

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

    // The util distance the walk height is not greater than the surface
    float edge = tan_theta * (depth.away - camera.origin.z - depth.height);
    float util = (length(displacement) - edge);

    // The quality of the parallax effect is how tiny the steps are
    float side = max(iResolution.x, iResolution.y);
    float quality = 1.0 / mix((side*0.05), (side*0.50), depth.quality);

    // Optimization: Low quality overshoot, high quality reverse
    float probe = (-1.0) / mix(50.0, 100.0, depth.quality);
    float i = 1.0;

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
                break;
            }
        }
    }

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

    // Depth of Field
    if (iDofEnable) {
        float intensity = iDofIntensity * pow(smoothstep(iDofStart, iDofEnd, 1.0 - depthflow.value), iDofExponent);
        vec4 color = fragColor;

        for (float angle=0.0; angle<TAU; angle+=TAU/iDofDirections) {
            for (float walk=1.0/iDofQuality; walk<=1.001; walk+=1.0/iDofQuality) {
                vec2 displacement = vec2(cos(angle), sin(angle)) * walk * intensity;
                color += gtexture(image, depthflow.gluv + displacement, depthflow.mirror);
            }
        }
        fragColor = color / (iDofDirections*iDofQuality);
    }

    // Vignette post processing
    if (iVigEnable) {
        vec2 away = astuv * (1.0 - astuv.yx);
        float linear = iVigIntensity * (away.x*away.y);
        fragColor.rgb *= clamp(pow(linear, iVigDecay), 0.0, 1.0);
    }

    // Colors post processing
    // Saturation
    float luminance = dot(fragColor.rgb, vec3(0.299, 0.587, 0.114));
    fragColor.rgb = mix(vec3(luminance), fragColor.rgb, iSaturation);
}
