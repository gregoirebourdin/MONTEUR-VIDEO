// Setty, the ManySetter mascot: a living DM bubble with an attitude.
// Built entirely in code with Three.js (no model file, no generated image), so every pose,
// expression and camera move is free and exact. The pose is a plain object of numbers that GSAP
// can tween; call `setty.apply(pose)` then render.
import * as THREE from "three";
import { DecalGeometry } from "three/addons/geometries/DecalGeometry.js";

// brand: logo gradient #ff884d → #e64b15, accent #ff611d (see manysetter-ad/film2/frame.md)
const TOP = new THREE.Color(0xffa066);
const BOTTOM = new THREE.Color(0xe64b15);
const INK = 0x1c1210;

// body: a puffy "squircle" bubble (superellipsoid), 2.8 wide, 2.3 high, 1.7 deep
const A = 1.4, B = 1.15, C = 0.85, P = 4.2, Q = 2.4;

/** z of the front surface at (x, y), in body space */
export function surfaceZ(x, y) {
  const s = Math.pow(Math.abs(x / A), P) + Math.pow(Math.abs(y / B), P);
  return s >= 1 ? 0 : C * Math.pow(1 - Math.pow(s, Q / P), 1 / Q);
}

function bodyColor(y) {
  const t = THREE.MathUtils.clamp(y / (2 * B) + 0.5, 0, 1);
  return BOTTOM.clone().lerp(TOP, Math.pow(t, 0.9));
}

function bodyGeometry() {
  const g = new THREE.SphereGeometry(1, 160, 96);
  const pos = g.attributes.position;
  const nrm = g.attributes.normal;
  const col = new Float32Array(pos.count * 3);
  const v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i);
    const ax = Math.abs(v.x), ay = Math.abs(v.y), az = Math.abs(v.z);
    const s = Math.pow(ax, P) + Math.pow(ay, P);
    const r = Math.pow(Math.pow(s, Q / P) + Math.pow(az, Q), -1 / Q);
    const x = v.x * r * A, y = v.y * r * B, z = v.z * r * C;
    pos.setXYZ(i, x, y, z);
    // analytic normal = gradient of the implicit surface (no seam on the sphere's join)
    const sx = Math.pow(Math.abs(x / A), P), sy = Math.pow(Math.abs(y / B), P);
    const S = sx + sy;
    let n;
    if (S < 1e-9) n = new THREE.Vector3(0, 0, Math.sign(z) || 1);
    else {
      const k = Math.pow(S, Q / P - 1);
      n = new THREE.Vector3(
        k * Math.pow(Math.abs(x / A), P - 1) * Math.sign(x) / A,
        k * Math.pow(Math.abs(y / B), P - 1) * Math.sign(y) / B,
        Math.pow(Math.abs(z / C), Q - 1) * Math.sign(z) / C,
      ).normalize();
    }
    nrm.setXYZ(i, n.x, n.y, n.z);
    const c = bodyColor(y);
    col.set([c.r, c.g, c.b], i * 3);
  }
  g.setAttribute("color", new THREE.BufferAttribute(col, 3));
  return g;
}

// the bubble's tail: a tapered, slightly curled horn at the bottom left, pointing down and OUT
function tailGeometry() {
  const h = 1.0;
  const g = new THREE.CylinderGeometry(0.06, 0.46, h, 64, 24);
  const pos = g.attributes.position;
  const col = new Float32Array(pos.count * 3);
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i);
    const t = (y + h / 2) / h; // 0 at the base, 1 at the tip
    pos.setX(i, pos.getX(i) + 0.32 * t * t); // curl the tip outward
    pos.setZ(i, pos.getZ(i) * 0.72);
    pos.setY(i, y + h / 2); // base at the origin
    const c = BOTTOM.clone().lerp(TOP, 0.12 * (1 - t));
    col.set([c.r, c.g, c.b], i * 3);
  }
  g.setAttribute("color", new THREE.BufferAttribute(col, 3));
  g.computeVertexNormals();
  return g;
}

// ---------- face texture: mouth, blush, tongue ----------
const FACE_W = 2.4, FACE_H = 1.0, PX = 427; // decal size in body units, pixels per unit

function drawFace(ctx, p) {
  const W = ctx.canvas.width, H = ctx.canvas.height;
  ctx.clearRect(0, 0, W, H);
  // blush
  for (const side of [-1, 1]) {
    const cx = W / 2 + side * 0.98 * PX, cy = H / 2 + 0.06 * PX;
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, 0.3 * PX);
    g.addColorStop(0, `rgba(255, 64, 104, ${0.8 * p.blush})`);
    g.addColorStop(1, "rgba(255, 70, 110, 0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.ellipse(cx, cy, 0.34 * PX, 0.22 * PX, 0, 0, Math.PI * 2);
    ctx.fill();
  }
  const mx = W / 2 + p.mouthX * PX, my = H / 2 + 0.04 * PX;
  ctx.save();
  ctx.translate(mx, my);
  ctx.rotate(p.mouthTilt);
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.strokeStyle = "#24140f";
  ctx.fillStyle = "#24140f";
  const w = 84 * p.mouthW;
  const sm = p.smirk; // >0 raises the right corner, <0 the left
  if (p.mouthOpen < 0.04) {
    // closed: a smile, a smirk, or a flat line (curve 0)
    ctx.lineWidth = 30;
    ctx.beginPath();
    ctx.moveTo(-w, -12 * p.curve - 26 * Math.max(0, -sm) + 8 * Math.max(0, sm));
    ctx.quadraticCurveTo(14 * sm, 46 * p.curve, w, -12 * p.curve - 30 * Math.max(0, sm) + 8 * Math.max(0, -sm));
    ctx.stroke();
    if (p.tongue > 0.02) {
      // blep: a little tongue under one corner of the smile
      ctx.save();
      ctx.translate(24, 18 * p.curve + 10);
      ctx.scale(1, p.tongue);
      ctx.fillStyle = "#ff5c80";
      ctx.beginPath();
      ctx.moveTo(-26, -8);
      ctx.lineTo(26, -8);
      ctx.bezierCurveTo(28, 40, -28, 40, -26, -8);
      ctx.fill();
      ctx.strokeStyle = "#24140f";
      ctx.lineWidth = 8;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(0, 16);
      ctx.stroke();
      ctx.restore();
      ctx.lineWidth = 26;
      ctx.beginPath();
      ctx.moveTo(-w, -12 * p.curve);
      ctx.quadraticCurveTo(14 * sm, 46 * p.curve, w, -12 * p.curve - 30 * Math.max(0, sm));
      ctx.stroke();
    }
  } else if (p.mouthRound > 0.5) {
    // "O" of surprise
    ctx.beginPath();
    ctx.ellipse(0, 14, 34 + 14 * p.mouthOpen, 24 + 46 * p.mouthOpen, 0, 0, Math.PI * 2);
    ctx.fill();
  } else {
    // open mouth: flat-ish top, round bottom, tongue, optional teeth
    const ow = w * 1.25, depth = 40 + 150 * p.mouthOpen;
    const lift = -26 * Math.max(0, sm);
    ctx.beginPath();
    ctx.moveTo(-ow, -14);
    ctx.quadraticCurveTo(0, 2 + 10 * p.curve, ow, -14 + lift);
    ctx.bezierCurveTo(ow * 0.9, depth, -ow * 0.9, depth, -ow, -14);
    ctx.closePath();
    ctx.fill();
    ctx.save();
    ctx.clip();
    if (p.teeth > 0.02) {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(-ow, -20, ow * 2, 22 * p.teeth);
    }
    ctx.fillStyle = "#ff5c80";
    ctx.beginPath();
    ctx.ellipse(6, depth * 0.78, ow * 0.62, depth * 0.42 * Math.max(0.3, p.tongue || 0.8), 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
  ctx.restore();
  // censor bar over the mouth when Setty swears (the bleep is in the mix)
  if (p.censor > 0.01) {
    ctx.save();
    ctx.translate(mx + 6, my + 8);
    ctx.rotate(-0.07);
    ctx.scale(p.censor, p.censor);
    const bw = 300, bh = 112;
    ctx.fillStyle = "#0d0c0a";
    ctx.beginPath();
    ctx.roundRect(-bw / 2, -bh / 2, bw, bh, 26);
    ctx.fill();
    ctx.fillStyle = "#ff7a3a";
    ctx.font = "800 72px Inter, Arial, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("#@!%", 0, 6);
    ctx.restore();
  }
}

// ---------- the default pose (every field is a number GSAP can tween, except `mouth`-free switches) ----------
export function basePose() {
  return {
    // whole body
    x: 0, y: 0, z: 0, turn: 0, tilt: 0, lean: 0, squash: 0, scale: 1,
    // eyes
    lookX: 0, lookY: 0, pupil: 1,
    lidL: 0.08, lidR: 0.08, lowL: 0, lowR: 0, slantL: 0, slantR: 0, happyL: 0, happyR: 0,
    browLy: 0, browRy: 0, browLr: 0, browRr: 0, brows: 1,
    // face
    curve: 1, smirk: 0, mouthW: 1, mouthOpen: 0, mouthRound: 0, mouthTilt: 0, mouthX: 0,
    teeth: 0, tongue: 0, blush: 0.6, censor: 0,
    // arms: raise 0 = hanging, 1.57 = out to the side, 3.1 = straight up; fwd swings to the front
    armLr: 0.35, armRr: 0.35, armLf: 0, armRf: 0, armLtw: 0, armRtw: 0,
    // typing dots above the head: phase drives the bounce, alert shows "!"
    dots: 1, dotsPhase: 0, dotsBounce: 0, alert: 0,
  };
}

// expression presets (merged over basePose); the face of the brand is `smug`
export const EXPRESSIONS = {
  happy: {},
  smug: { lidL: 0.56, lidR: 0.44, slantL: -0.14, slantR: 0.1, browLy: 0.15, browLr: 0.26, browRy: -0.04, browRr: -0.1,
          smirk: 1, curve: 0.7, mouthX: 0.08, lookX: 0.35, blush: 0.4, lean: -0.04 },
  sideEye: { lidL: 0.5, lidR: 0.5, lookX: 0.9, lookY: -0.05, curve: 0, mouthW: 0.7, smirk: -0.3, browLy: -0.02, browRy: 0.08,
             browRr: -0.1, blush: 0.25 },
  shocked: { lidL: 0, lidR: 0, pupil: 0.62, browLy: 0.2, browRy: 0.2, browLr: -0.1, browRr: -0.1, mouthOpen: 0.85, mouthRound: 1,
             blush: 0.2, dots: 0, alert: 1, armLr: 1.2, armRr: 1.2 },
  laughing: { happyL: 1, happyR: 1, browLy: 0.12, browRy: 0.12, mouthOpen: 1, teeth: 1, tongue: 0.9,
              blush: 1, tilt: -0.08 },
  unimpressed: { lidL: 0.48, lidR: 0.48, lookY: 0.85, lookX: -0.15, curve: 0, mouthW: 0.8, smirk: 0.25, browLy: 0.05, browRy: 0.05,
                 blush: 0.2 },
  wink: { happyR: 1, lidL: 0.1, smirk: 0.4, tongue: 1, curve: 1.1, blush: 0.8, browRy: -0.04, browLy: 0.1, armRr: 2.6 },
  excuseMe: { lidL: 0.3, lidR: 0.3, slantL: 0.25, slantR: -0.25, browLy: -0.05, browRy: -0.05, browLr: -0.32, browRr: 0.32,
              curve: -0.6, mouthW: 0.75, blush: 0.3, armLr: 1.25, armRr: 1.25, armLf: 0.5, armRf: 0.5, lean: 0.06 },
  proud: { lidL: 0.3, lidR: 0.3, lowL: 0.4, lowR: 0.4, browLy: 0.08, browRy: 0.08, curve: 1.25, mouthW: 1.15, blush: 0.9,
           tilt: -0.12, armLr: 0.6, armRr: 0.6, armLf: -0.6, armRf: -0.6 },
};

export function pose(name, extra = {}) {
  return Object.assign(basePose(), EXPRESSIONS[name] || {}, extra);
}

export function createSetty() {
  const root = new THREE.Group(); // origin on the floor under the body
  const body = new THREE.Group();
  body.position.y = B + 0.55; // Setty hovers: a DM bubble floats, and its tail can point down
  root.add(body);

  const skin = new THREE.MeshPhysicalMaterial({
    vertexColors: true, roughness: 0.3, clearcoat: 1, clearcoatRoughness: 0.14,
    sheen: 0.45, sheenColor: new THREE.Color(0xffc29a), sheenRoughness: 0.45,
  });
  const lidSkin = new THREE.MeshPhysicalMaterial({
    color: bodyColor(-0.35), roughness: 0.3, clearcoat: 1, clearcoatRoughness: 0.14,
  });
  const shell = new THREE.Mesh(bodyGeometry(), skin);
  shell.castShadow = true;
  body.add(shell);

  const tail = new THREE.Mesh(tailGeometry(), skin);
  // the horn is built tip-up (+y); rotating by θ sends +y to (-sin θ, cos θ) = (-0.7, -0.71):
  // the tip points down and OUT to the left, and the curl lifts it slightly, like a chat bubble's tail
  tail.rotation.z = Math.PI - Math.asin(0.7);
  tail.position.set(-0.82, -0.74, 0);
  tail.castShadow = true;
  body.add(tail);

  // face decal (mouth, blush), projected on the front of the shell
  const faceCanvas = document.createElement("canvas");
  faceCanvas.width = Math.round(FACE_W * PX);
  faceCanvas.height = Math.round(FACE_H * PX);
  const faceCtx = faceCanvas.getContext("2d");
  const faceTex = new THREE.CanvasTexture(faceCanvas);
  faceTex.colorSpace = THREE.SRGBColorSpace;
  faceTex.anisotropy = 8;
  shell.updateMatrixWorld(true);
  const decal = new THREE.Mesh(
    new DecalGeometry(shell, new THREE.Vector3(0, -0.42, 0.8), new THREE.Euler(0, 0, 0), new THREE.Vector3(FACE_W, FACE_H, 1.2)),
    new THREE.MeshPhysicalMaterial({
      map: faceTex, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4,
      roughness: 0.32, clearcoat: 1, clearcoatRoughness: 0.12,
    }),
  );
  body.add(decal);

  // eyes: glossy balls, pupils that look around, real lids (upper + lower) in skin colour
  const white = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.12, clearcoat: 1 });
  const ink = new THREE.MeshPhysicalMaterial({ color: INK, roughness: 0.18, clearcoat: 1 });
  const glint = new THREE.MeshBasicMaterial({ color: 0xffffff });
  const ER = 0.37;
  const eyes = [];
  for (const side of [-1, 1]) {
    const ex = side * 0.52, ey = 0.06;
    const eye = new THREE.Group();
    eye.position.set(ex, ey, surfaceZ(ex, ey) - 0.12);
    eye.scale.set(1, 1.1, 0.62);
    const ball = new THREE.Mesh(new THREE.SphereGeometry(ER, 64, 48), white);
    const pupilPivot = new THREE.Group();
    // pupil and glints stay inside the lid's radius, so a closed lid really hides them
    const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.255, 64, 48), ink);
    pupil.scale.set(1, 1.08, 0.5);
    pupil.position.z = ER - 0.122;
    const g1 = new THREE.Mesh(new THREE.CircleGeometry(0.075, 32), glint);
    g1.position.set(-0.075, 0.09, ER - 0.002);
    const g2 = new THREE.Mesh(new THREE.CircleGeometry(0.033, 24), glint);
    g2.position.set(0.085, -0.1, ER - 0.002);
    pupilPivot.add(pupil, g1, g2);
    const capGeo = (top) => new THREE.SphereGeometry(ER * 1.07, 64, 32, 0, Math.PI * 2, top ? 0 : Math.PI / 2, Math.PI / 2);
    // a dark lash line on the edge of each lid: hidden inside the head while the eye is open,
    // a lid line when half-closed, a "^" (lower lid up) or "u" (upper lid down) when closed
    const lash = () => {
      const g = new THREE.TorusGeometry(ER * 1.07, 0.024, 10, 64, Math.PI - 1.2);
      g.rotateZ(0.6); // trimmed ends: the corners sit on the hinge and would poke out of the head
      const r = new THREE.Mesh(g, ink);
      r.rotation.x = Math.PI / 2; // front half of the lid's rim
      return r;
    };
    // closed eyes drawn on the closed lid: "^" when happy, "u" when blinking
    const closedArc = (happy) => {
      const g = new THREE.TorusGeometry(0.27, 0.034, 12, 48, 2.1);
      g.rotateZ(Math.PI / 2 - 1.05);
      g.translate(0, -0.27, 0);
      if (!happy) g.rotateZ(Math.PI);
      const m = new THREE.Mesh(g, ink);
      m.position.set(0, happy ? 0.08 : -0.06, ER * 1.07 - 0.015);
      m.visible = false;
      return m;
    };
    const happyArc = closedArc(true);
    const blinkArc = closedArc(false);
    const upperSlant = new THREE.Group();
    const upper = new THREE.Mesh(capGeo(true), lidSkin);
    upper.add(lash());
    upperSlant.add(upper);
    const lowerSlant = new THREE.Group();
    const lower = new THREE.Mesh(capGeo(false), lidSkin);
    lower.add(lash());
    lowerSlant.add(lower);
    eye.add(ball, pupilPivot, upperSlant, lowerSlant, happyArc, blinkArc);
    body.add(eye);

    const browGeo = new THREE.TorusGeometry(0.42, 0.058, 16, 48, 0.78);
    browGeo.rotateZ(Math.PI / 2 - 0.39);
    browGeo.translate(0, -0.42, 0);
    const brow = new THREE.Mesh(browGeo, ink);
    brow.scale.set(1, 1, 0.55);
    const browPivot = new THREE.Group();
    browPivot.add(brow);
    body.add(browPivot);
    eyes.push({ side, ex, ey, pupilPivot, pupil, upper, lower, upperSlant, lowerSlant, browPivot, happyArc, blinkArc });
  }

  // stubby arms
  const arms = [];
  for (const side of [-1, 1]) {
    const shoulder = new THREE.Group();
    shoulder.position.set(side * 1.3, -0.22, 0.05);
    const arm = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 0.36, 12, 32), skin);
    arm.geometry.translate(0, -0.3, 0);
    arm.castShadow = true;
    // arm vertex colours (mid orange)
    const c = bodyColor(-0.3);
    const n = arm.geometry.attributes.position.count;
    arm.geometry.setAttribute("color", new THREE.BufferAttribute(new Float32Array(n * 3).map((_, i) => [c.r, c.g, c.b][i % 3]), 3));
    shoulder.add(arm);
    body.add(shoulder);
    arms.push({ side, shoulder });
  }

  // typing dots, and the "!" that replaces them when Setty is shocked
  const dotMat = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.18, clearcoat: 1, emissive: 0xffe6d6, emissiveIntensity: 0.2 });
  const dotsGroup = new THREE.Group();
  dotsGroup.position.set(0, B + 0.48, 0.15);
  const dots = [0, 1, 2].map((i) => {
    const d = new THREE.Mesh(new THREE.SphereGeometry(0.135, 32, 24), dotMat);
    d.position.x = (i - 1) * 0.4;
    d.castShadow = true;
    dotsGroup.add(d);
    return d;
  });
  body.add(dotsGroup);
  const bang = new THREE.Group();
  const bangBar = new THREE.Mesh(new THREE.CapsuleGeometry(0.11, 0.42, 8, 24), dotMat);
  bangBar.position.y = 0.3;
  const bangDot = new THREE.Mesh(new THREE.SphereGeometry(0.12, 32, 24), dotMat);
  bangDot.position.y = -0.18;
  bang.add(bangBar, bangDot);
  bang.position.set(0, B + 0.42, 0.15);
  bang.scale.setScalar(0.85);
  body.add(bang);

  function apply(p) {
    root.position.set(p.x, p.y, p.z);
    const s = p.squash;
    root.scale.set(p.scale * (1 + s * 0.6), p.scale * (1 - s), p.scale * (1 + s * 0.6));
    root.rotation.set(0, p.turn, 0);
    body.rotation.set(p.tilt, 0, p.lean);

    for (const e of eyes) {
      const L = e.side < 0;
      const happy = (L ? p.happyL : p.happyR) > 0.5;
      const lid = happy ? 1 : L ? p.lidL : p.lidR, low = happy ? 0 : L ? p.lowL : p.lowR, slant = happy ? 0 : L ? p.slantL : p.slantR;
      e.happyArc.visible = happy;
      e.blinkArc.visible = !happy && lid > 0.9;
      e.pupilPivot.rotation.set(-p.lookY * 0.42, p.lookX * 0.5, 0);
      e.pupil.scale.set(p.pupil, 1.08 * p.pupil, 0.5);
      e.upperSlant.rotation.z = slant * e.side * -1;
      e.lowerSlant.rotation.z = slant * e.side * -1;
      // upper cap: -1.5 rad hides it behind the eye, +1.55 closes the eye
      e.upper.rotation.x = THREE.MathUtils.lerp(-1.5, 1.57, THREE.MathUtils.clamp(lid, 0, 1));
      e.lower.rotation.x = THREE.MathUtils.lerp(1.5, -1.57, THREE.MathUtils.clamp(low, 0, 1));
      const by = L ? p.browLy : p.browRy, br = L ? p.browLr : p.browRr;
      const bx = e.ex * 1.0, byy = e.ey + 0.52 + by;
      e.browPivot.position.set(bx, byy, surfaceZ(bx, byy) + 0.035);
      e.browPivot.rotation.set(-0.15, 0, br * -e.side);
      e.browPivot.visible = p.brows > 0.5;
    }

    for (const a of arms) {
      const L = a.side < 0;
      const r = L ? p.armLr : p.armRr, f = L ? p.armLf : p.armRf, tw = L ? p.armLtw : p.armRtw;
      a.shoulder.rotation.set(-f, -tw * a.side, r * a.side, "YXZ");
    }

    dotsGroup.visible = p.dots > 0.5;
    dots.forEach((d, i) => {
      d.position.y = Math.max(0, Math.sin(p.dotsPhase - i * 0.9)) * 0.17 * p.dotsBounce;
    });
    bang.visible = p.alert > 0.01;
    bang.scale.setScalar(Math.max(0.001, 0.85 * p.alert));

    drawFace(faceCtx, p);
    faceTex.needsUpdate = true;
  }

  apply(basePose());
  return { root, apply };
}

/** standard studio lighting for Setty: warm key with soft shadow, orange rims, environment reflections */
export async function setupStage(renderer, scene, { ground = -0.001, shadowOpacity = 0.32 } = {}) {
  const { RoomEnvironment } = await import("three/addons/environments/RoomEnvironment.js");
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.95;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.55;

  const key = new THREE.DirectionalLight(0xfff1e6, 2.5);
  key.position.set(-3, 6, 6);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.radius = 10;
  key.shadow.bias = -0.0004;
  Object.assign(key.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6, near: 0.5, far: 30 });
  scene.add(key);
  const rim = new THREE.DirectionalLight(0xff8a4c, 3.0);
  rim.position.set(3.5, 2.5, -4);
  scene.add(rim);
  const rim2 = new THREE.DirectionalLight(0xffc7a0, 1.3);
  rim2.position.set(-4, 1.5, -3);
  scene.add(rim2);
  scene.add(new THREE.HemisphereLight(0xffe2cc, 0x2a1a12, 0.5));

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.ShadowMaterial({ opacity: shadowOpacity }));
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = ground;
  floor.receiveShadow = true;
  scene.add(floor);
  return { key, rim, floor };
}
