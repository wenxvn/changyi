import { useEffect, useRef } from "react";
import {
  AmbientLight,
  BufferAttribute,
  BufferGeometry,
  Color,
  DirectionalLight,
  Group,
  Mesh,
  MeshBasicMaterial,
  MeshPhysicalMaterial,
  PerspectiveCamera,
  Points,
  PointsMaterial,
  Scene,
  SphereGeometry,
  TorusGeometry,
  WebGLRenderer,
} from "three";
import type { AgentStage } from "./types";

export function AgentScene({ stage, onError }: { stage: AgentStage; onError: () => void }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const stageRef = useRef(stage);
  const errorRef = useRef(onError);

  useEffect(() => { stageRef.current = stage; }, [stage]);
  useEffect(() => { errorRef.current = onError; }, [onError]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let renderer: WebGLRenderer;
    try {
      renderer = new WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: "low-power" });
    } catch {
      errorRef.current();
      return;
    }

    const root = document.documentElement;
    const readColor = (token: string, fallback: string) => {
      const value = getComputedStyle(root).getPropertyValue(token).trim();
      return new Color(value || fallback);
    };
    const teal = readColor("--agent-core", "#0d7a75");
    const tealDeep = readColor("--accent-primary", "#0d7a75");
    const blue = readColor("--accent-secondary", "#2563eb");
    const scene = new Scene();
    const camera = new PerspectiveCamera(35, 1, 0.1, 20);
    camera.position.set(0, 0, 4.6);
    const assembly = new Group();
    scene.add(assembly);

    const ambient = new AmbientLight(0xffffff, 2.1);
    const keyLight = new DirectionalLight(0xffffff, 3.2);
    keyLight.position.set(-2.4, 3.4, 5);
    const edgeLight = new DirectionalLight(blue, 2.2);
    edgeLight.position.set(2.5, -1, -2);
    scene.add(ambient, keyLight, edgeLight);

    const coreMaterial = new MeshPhysicalMaterial({
      color: teal,
      emissive: tealDeep,
      emissiveIntensity: 0.12,
      roughness: 0.26,
      metalness: 0.08,
      clearcoat: 0.78,
      clearcoatRoughness: 0.14,
      transparent: true,
      opacity: 0.94,
    });
    const core = new Mesh(new SphereGeometry(0.8, 40, 32), coreMaterial);
    assembly.add(core);

    const inner = new Mesh(
      new SphereGeometry(0.65, 32, 24),
      new MeshBasicMaterial({ color: teal, transparent: true, opacity: 0.08, wireframe: true }),
    );
    inner.rotation.set(0.3, 0.2, 0.1);
    assembly.add(inner);

    const orbitMaterial = new MeshBasicMaterial({ color: blue, transparent: true, opacity: 0.5 });
    const orbitA = new Mesh(new TorusGeometry(1.14, 0.008, 6, 120), orbitMaterial);
    orbitA.rotation.set(1.08, 0.1, -0.48);
    const orbitB = new Mesh(new TorusGeometry(1.24, 0.006, 6, 120), orbitMaterial.clone());
    orbitB.rotation.set(0.38, 1.2, 0.7);
    assembly.add(orbitA, orbitB);

    const particleCount = 15;
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i += 1) {
      const angle = (Math.PI * 2 * i) / particleCount;
      const radius = 1.42 + (i % 3) * 0.11;
      positions[i * 3] = Math.cos(angle) * radius;
      positions[i * 3 + 1] = Math.sin(angle) * radius * 0.68;
      positions[i * 3 + 2] = Math.sin(angle * 1.7) * 0.34;
    }
    const particlesGeometry = new BufferGeometry();
    particlesGeometry.setAttribute("position", new BufferAttribute(positions, 3));
    const particles = new Points(
      particlesGeometry,
      new PointsMaterial({ color: teal, size: 0.055, transparent: true, opacity: 0.82, sizeAttenuation: true }),
    );
    assembly.add(particles);

    const resize = () => {
      const width = Math.max(canvas.clientWidth, 1);
      const height = Math.max(canvas.clientHeight, 1);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.render(scene, camera);
    };
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(canvas);
    resize();

    let elapsed = 0;
    let lastFrame = 0;
    const animate = (time: number) => {
      if (document.hidden || time - lastFrame < 33) return;
      lastFrame = time;
      elapsed += 0.033;
      const currentStage = stageRef.current;
      const targetScale = currentStage === "submitting" ? 0.88 : currentStage === "waiting" ? 0.96 : 1;
      const breathe = currentStage === "idle" || currentStage === "composing" ? Math.sin(elapsed * 1.15) * 0.025 : 0;
      assembly.scale.setScalar(targetScale + breathe);
      core.rotation.y += currentStage === "composing" ? 0.002 : 0.0012;
      core.rotation.x = Math.sin(elapsed * 0.42) * 0.035;
      orbitA.rotation.z += currentStage === "submitting" ? 0.0032 : 0.001;
      orbitB.rotation.x += currentStage === "waiting" ? 0.0022 : 0.0007;
      particles.rotation.z -= currentStage === "submitting" ? 0.006 : 0.0014;
      renderer.render(scene, camera);
    };
    const updateVisibility = () => renderer.setAnimationLoop(document.hidden ? null : animate);
    document.addEventListener("visibilitychange", updateVisibility);
    renderer.setAnimationLoop(animate);

    return () => {
      document.removeEventListener("visibilitychange", updateVisibility);
      resizeObserver.disconnect();
      renderer.setAnimationLoop(null);
      scene.traverse((object) => {
        const renderable = object as Mesh;
        renderable.geometry?.dispose?.();
        const material = renderable.material;
        if (Array.isArray(material)) material.forEach((item) => item.dispose());
        else material?.dispose?.();
      });
      renderer.dispose();
      renderer.forceContextLoss();
    };
  }, []);

  return <canvas ref={canvasRef} className="care-agent__canvas" aria-hidden="true" />;
}
