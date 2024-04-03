/*
// (c) 2023 CC BY-SA 4.0, Tremeschin
*/

// This is the old and original DepthFlow shader before Camera
// Kept as a simpler older relic of the past

// ------------------------------------------------------------------------------------------------|

// Get the clamped depth of a image (no overshooting) based on iFocus
// - Zero depth means the object does not move
float get_depth(vec2 stuv, sampler2D depth) {
    return iFocus - draw_image(depth, stuv).r;
}

// Depth-Layer displacement for a pixel, composed of the camera displacement times max
// camera displacement (iParallaxFactor) times the depth of the pixel (zero should not move)
vec2 displacement(vec2 stuv, sampler2D depth) {
    return iPosition * get_depth(stuv, depth) * iParallaxFactor;
}

// ------------------------------------------------------------------------------------------------|

// Apply the DepthFlow parallax effect into some image and its depth map
//
// - The idea of how this shader works is that we search, on the opposite direction a pixel is
//   supposed to "walk", if some other pixel should be in front of *us* or not.
//
vec4 image_parallax(vec2 stuv, sampler2D image, sampler2D depth) {

    // The direction the pixel walk is the camera displacement itself
    vec2 direction = iPosition * iParallaxFactor;

    // Initialize the parallax space with the original stuv
    vec2 parallax_uv = stuv + displacement(stuv, depth);

    // The quality of the parallax effect is how tiny the steps are
    float quality;
    switch (iQuality) {
        case 0: quality = 0.01;   break;
        case 1: quality = 0.005;  break;
        case 2: quality = 0.001;  break;
        case 3: quality = 0.0008; break;
        case 4: quality = 0.0005; break;
    }

    // FIXME: Do you know how to code shaders better than me? Can this be more efficient?
    for (float i=0; i<length(direction); i=i+quality) {
        vec2 walk_stuv          = stuv + direction*i;
        vec2 other_displacement = displacement(walk_stuv, depth);

        // This pixel is on top of us, update the parallax stuv
        if (i < length(other_displacement)) {
            parallax_uv = walk_stuv;
        }
    }

    // Sample the texture on the parallax space
    return draw_image(image, parallax_uv);
}

// ------------------------------------------------------------------------------------------------|

void main() {
    vec2 uv = zoom(stuv, 0.95 + 0.05*iZoom, vec2(0.5));
    fragColor = image_parallax(uv, image, depth);
}
