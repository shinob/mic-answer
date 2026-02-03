import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';

// Bridge object for communication with main UI
window.vrmBridge = {
  outputRms: 0,
  status: 'idle',
};

const container = document.getElementById('vrm-container');
if (!container) throw new Error('#vrm-container not found');

// Renderer
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

// Scene (transparent to show CSS background)
const scene = new THREE.Scene();

// Camera
const camera = new THREE.PerspectiveCamera(20, container.clientWidth / container.clientHeight, 0.1, 50);
camera.position.set(0, 1.35, 1.5);
camera.lookAt(0, 1.25, 0);

// Lights
const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
dirLight.position.set(1, 2, 2);
scene.add(dirLight);
const fillLight = new THREE.DirectionalLight(0xffffff, 0.5);
fillLight.position.set(-1, 1, 1);
scene.add(fillLight);
scene.add(new THREE.AmbientLight(0xffffff, 1.0));

// Model state
let vrm = null;       // set if VRM data is present
let glbModel = null;   // set if plain GLB (no VRM)
let mixer = null;      // AnimationMixer for GLB animations
const clock = new THREE.Clock();

const loader = new GLTFLoader();
loader.register((parser) => new VRMLoaderPlugin(parser));

// Set natural resting pose (arms down from T-pose)
function setRestPose(vrm, metaVersion) {
  const humanoid = vrm.humanoid;
  if (!humanoid) return;

  const leftUpper = humanoid.getNormalizedBoneNode('leftUpperArm');
  const rightUpper = humanoid.getNormalizedBoneNode('rightUpperArm');
  const leftLower = humanoid.getNormalizedBoneNode('leftLowerArm');
  const rightLower = humanoid.getNormalizedBoneNode('rightLowerArm');
  if (!leftUpper && !rightUpper) return;

  // VRM 1.0 uses positive sign, VRM 0.x uses negative
  const sign = (metaVersion === '1') ? 1 : -1;
  //console.log(`Rest pose: metaVersion=${metaVersion}, sign=${sign}`);

  if (leftUpper)  leftUpper.rotation.z  = -1.3 * sign;
  if (rightUpper) rightUpper.rotation.z =  1.3 * sign;
  if (leftLower)  leftLower.rotation.z  =  0.15 * sign;
  if (rightLower) rightLower.rotation.z = -0.15 * sign;
}

// Auto-fit camera to upper body (bust shot)
function fitCameraToModel(object) {
  const box = new THREE.Box3().setFromObject(object);
  const size = box.getSize(new THREE.Vector3());
  const min = box.min;
  const max = box.max;

  // Focus on upper 40% of the model (chest and above)
  const bustY = min.y + size.y * 0.6;
  const focusCenter = new THREE.Vector3(
    (min.x + max.x) / 2,
    (bustY + max.y) / 2 + 0.05,  // offset down
    (min.z + max.z) / 2
  );
  const frameHeight = max.y - bustY;

  const fov = camera.fov * (Math.PI / 180);
  let dist = (frameHeight / 2) / Math.tan(fov / 2);
  dist *= 1.2; // padding (lower = more zoom)

  camera.position.set(focusCenter.x, focusCenter.y, focusCenter.z + dist);
  camera.lookAt(focusCenter);
  camera.near = dist / 100;
  camera.far = dist * 100;
  camera.updateProjectionMatrix();

  console.log('Camera fitted (bust):', focusCenter, 'dist=', dist);
}

function loadModel(url) {
  return new Promise((resolve, reject) => {
    console.log('Loading model:', url);
    loader.load(
      url,
      (gltf) => {
        if (gltf.userData.vrm) {
          try {
            vrm = gltf.userData.vrm;
            const metaVersion = vrm.meta?.metaVersion || '0';
            console.log('VRM meta version:', metaVersion);
            if (metaVersion === '0') {
              VRMUtils.rotateVRM0(vrm);
            }
            scene.add(vrm.scene);
            setRestPose(vrm, metaVersion);
            vrm.update(0);
            fitCameraToModel(vrm.scene);
            console.log('VRM model loaded:', url);
            resolve();
            return;
          } catch (e) {
            console.warn('VRM processing failed:', e);
            vrm = null;
          }
        }
        // Plain GLB path
        glbModel = gltf.scene;
        scene.add(glbModel);
        fitCameraToModel(glbModel);
        if (gltf.animations.length > 0) {
          mixer = new THREE.AnimationMixer(glbModel);
          for (const clip of gltf.animations) {
            mixer.clipAction(clip).play();
          }
        }
        console.log('GLB model loaded:', url);
        resolve();
      },
      undefined,
      (err) => {
        console.warn('Failed to load', url, err);
        reject(err);
      }
    );
  });
}

// Try each model file in order; skip to next on failure
async function detectAndLoadModel() {
  const cacheBust = '?t=' + Date.now();
  const candidates = ['/static/model.vrm', '/static/model.glb'];
  for (const path of candidates) {
    try {
      const resp = await fetch(path + cacheBust, { method: 'HEAD' });
      if (!resp.ok) continue;
      await loadModel(path + cacheBust);
      return; // success
    } catch (e) {
      console.warn('Skipping', path, ':', e);
    }
  }
  console.error('No model could be loaded');
}

detectAndLoadModel();

// Blink state
let blinkTimer = 0;
let nextBlinkAt = randomBlink();
let blinkPhase = 0; // 0=open, 1=closing, 2=opening

function randomBlink() {
  return 2 + Math.random() * 4; // 2-6 seconds
}

// Animation loop
function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  const elapsed = clock.getElapsedTime();

  if (vrm) {
    vrm.update(delta);

    const expr = vrm.expressionManager;
    if (expr) {
      // --- Lip sync ---
      const rms = window.vrmBridge.outputRms || 0;
      const status = window.vrmBridge.status || 'idle';
      const speaking = status === 'playing' && rms > 0.001;

      if (speaking) {
        const intensity = Math.min(rms / 0.05, 1.0);
        const t = elapsed * 8;
        const aaVal = intensity * (0.5 + 0.5 * Math.sin(t));
        const ohVal = intensity * (0.5 + 0.5 * Math.cos(t * 1.3));
        expr.setValue('aa', aaVal);
        expr.setValue('oh', ohVal * 0.4);
      } else {
        const curAa = expr.getValue('aa') || 0;
        const curOh = expr.getValue('oh') || 0;
        expr.setValue('aa', curAa * 0.85);
        expr.setValue('oh', curOh * 0.85);
      }

      // --- Blink ---
      blinkTimer += delta;
      if (blinkPhase === 0 && blinkTimer >= nextBlinkAt) {
        blinkPhase = 1;
        blinkTimer = 0;
      }

      if (blinkPhase === 1) {
        const v = Math.min(blinkTimer / 0.06, 1.0);
        expr.setValue('blink', v);
        if (v >= 1.0) { blinkPhase = 2; blinkTimer = 0; }
      } else if (blinkPhase === 2) {
        const v = 1.0 - Math.min(blinkTimer / 0.08, 1.0);
        expr.setValue('blink', v);
        if (v <= 0) {
          blinkPhase = 0;
          blinkTimer = 0;
          nextBlinkAt = randomBlink();
        }
      }
    }

    // --- Breathing (spine bone) ---
    const spine = vrm.humanoid?.getNormalizedBoneNode('spine');
    if (spine) {
      const breathe = Math.sin(elapsed * 1.8) * 0.008;
      spine.rotation.x = breathe;
    }

    // --- Subtle head movement ---
    const head = vrm.humanoid?.getNormalizedBoneNode('head');
    if (head) {
      head.rotation.x = Math.sin(elapsed * 0.7) * 0.015;
      head.rotation.y = Math.sin(elapsed * 0.5) * 0.01;
    }
  }

  // GLB animation mixer
  if (mixer) {
    mixer.update(delta);
  }

  renderer.render(scene, camera);
}

animate();

// Resize
const onResize = () => {
  const w = container.clientWidth;
  const h = container.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
};
window.addEventListener('resize', onResize);
