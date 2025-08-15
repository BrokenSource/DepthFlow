function loadParticles() {
  tsParticles.load("tsparticles", {
    autoPlay: true,
    fullScreen: {
      enable: false,
      zIndex: 0
    },
    detectRetina: true,
    fpsLimit: 60,
    interactivity: {
      detectsOn: "window",
      events: {
        onHover: {
          enable: true,
          parallax: {
            enable: true,
            force: 100,
            smooth: 10
          }
        }
      },
    },
    particles: {
      color: {value: "#333"},
      links: {
        color: {value: "#777"},
        distance: 300,
        enable: true,
        opacity: 0.2,
        width: 2
      },
      move: {
        direction: "none",
        enable: true,
        random: true,
        straight: false,
        speed: 0.4,
      },
      number: {
        density: {
          enable: true,
          area: 2000
        },
        value: 80
      },
      opacity: {
        value: {min: 0.05, max: 0.1},
        animation: {
          enable: true,
          speed: 0.2,
          minimumValue: 0.05
        }
      },
      size: {
        value: {min: 1, max: 5}
      }
    },
    pauseOnBlur: true,
    pauseOnOutsideViewport: true,
    zLayers: 100,
  });
}

// Translate particles on scroll
document.addEventListener('DOMContentLoaded', function() {
  const particles = document.getElementById('tsparticles');
  if (!particles) return;
  loadParticles();
  window.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset || document.documentElement.scrollTop;
    particles.style.transform = `translateY(${-0.1*scrolled}px)`;
  });
});