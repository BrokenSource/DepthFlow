/*
// (c) 2024 CC BY-SA 4.0, Tremeschin
*/

// Note: Experimental DepthFlow shader using Ray Marching concepts
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

    // Angle between plane norm (0, 0, 1) and the ray
    vec3 direction = normalize(iCamera.target - iCamera.origin - iCamera.position);
    float theta = acos(dot(vec3(0, 0, 1), direction));
    float phi   = (1 - iCamera.origin.z - iParallaxHeight) / cos(theta);
    float tau   = (1 - iCamera.origin.z) / cos(theta);
    float walk  = max(0, (tau - phi));
    vec3  ray   = iCamera.origin + (phi*direction);
    vec3  march = (tau - phi)*direction;

    // The quality of the parallax effect is how tiny the steps are
    const float min_step = 0.005;
    const float max_step = 0.0006;
    float quality = mix(min_step, max_step, iQuality);
    vec2 parallax = ray.xy;

    for (float i=0.0; i<walk+quality; i+=quality) {
        vec3 sample = ray + i*direction;
        sample.xy = gluv2stuv(sample.xy);
        float depth_height = iParallaxHeight * draw_image(depth, sample.xy).r;
        float walk_height  = 1 - sample.z;

        if (walk_height <= depth_height) {
            parallax = sample.xy;
            break;
        }
    }

    fragColor = draw_image(image, parallax);
}

