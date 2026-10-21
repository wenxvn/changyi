import { useEffect, useRef } from "react";
import {
  AmbientLight,
  Color,
  DirectionalLight,
  Mesh,
  MeshPhysicalMaterial,
  PerspectiveCamera,
  PointLight,
  Scene,
  SphereGeometry,
  WebGLRenderer,
} from "three";
import type { TriageStatus } from "../../types/api";

interface SafetyGateOrbProps {
  status: TriageStatus;
  size?: "small" | "medium" | "large";
  animated?: boolean;
}

const STATUS_COLORS: Record<TriageStatus, { core: string; glow: string; label: string }> = {
  EMERGENCY: { core: "#dc2626", glow: "#ef4444", label: "需要优先评估" },
  URGENT: { core: "#d97706", glow: "#f59e0b", label: "建议尽快评估" },
  ROUTINE: { core: "#059669", glow: "#10b981", label: "可继续了解路径" },
  INSUFFICIENT_INFORMATION: { core: "#6b7280", glow: "#9ca3af", label: "需要补充信息" },
};

const SIZE_MAP = {
  small: 180,
  medium: 280,
  large: 380,
};

export function SafetyGateOrb({ status, size = "large", animated = true }: SafetyGateOrbProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const statusRef = useRef(status);
  const sizeRef = useRef(size);

  useEffect(() => { statusRef.current = status; }, [status]);
  useEffect(() => { sizeRef.current = size; }, [size]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !animated) return;

    let renderer: WebGLRenderer;
    try {
      renderer = new WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: "low-power" });
    } catch {
      return;
    }

    const scene = new Scene();
    const camera = new PerspectiveCamera(35, 1, 0.1, 20);
    camera.position.set(0, 0, 5.5);

    const ambient = new AmbientLight(0xffffff, 1.8);
    const keyLight = new DirectionalLight(0xffffff, 2.5);
    keyLight.position.set(-3, 4, 6);
    const edgeLight = new DirectionalLight(0xffffff, 1.8);
    edgeLight.position.set(3, -2, -3);
    scene.add(ambient, keyLight, edgeLight);

    const pointLight = new PointLight(0xffffff, 180, 10);
    pointLight.position.set(0, 0, 0);
    scene.add(pointLight);

    const geometry = new SphereGeometry(1.2, 64, 48);
    const material = new MeshPhysicalMaterial({
      color: new Color(STATUS_COLORS.ROUTINE.core),
      emissive: new Color(STATUS_COLORS.ROUTINE.glow),
      emissiveIntensity: 0.3,
      roughness: 0.15,
      metalness: 0.1,
      clearcoat: 0.9,
      clearcoatRoughness: 0.1,
      transparent: true,
      opacity: 0.95,
    });
    const orb = new Mesh(geometry, material);
    scene.add(orb);

    const resize = () => {
      const width = Math.max(canvas.clientWidth, 1);
      const height = Math.max(canvas.clientHeight, 1);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
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

      const currentStatus = statusRef.current;
      const colors = STATUS_COLORS[currentStatus];
      material.color.lerp(new Color(colors.core), 0.05);
      material.emissive.lerp(new Color(colors.glow), 0.05);

      if (currentStatus === "EMERGENCY") {
        const pulse = Math.sin(elapsed * 3.5) * 0.4 + 0.6;
        material.emissiveIntensity = 0.6 + pulse * 0.4;
        orb.scale.setScalar(1 + Math.sin(elapsed * 3.5) * 0.08);
        pointLight.intensity = 200 + pulse * 100;
      } else if (currentStatus === "URGENT") {
        material.emissiveIntensity = 0.4 + Math.sin(elapsed * 2.2) * 0.15;
        orb.scale.setScalar(1 + Math.sin(elapsed * 2.2) * 0.04);
        pointLight.intensity = 160 + Math.sin(elapsed * 2.2) * 40;
      } else if (currentStatus === "ROUTINE") {
        material.emissiveIntensity = 0.25 + Math.sin(elapsed * 1.2) * 0.08;
        orb.scale.setScalar(1 + Math.sin(elapsed * 1.2) * 0.02);
        pointLight.intensity = 140;
      } else {
        material.emissiveIntensity = 0.15;
        orb.scale.setScalar(1);
        pointLight.intensity = 100;
      }

      orb.rotation.y += 0.003;
      orb.rotation.x = Math.sin(elapsed * 0.3) * 0.1;

      renderer.render(scene, camera);
    };
    const updateVisibility = () => renderer.setAnimationLoop(document.hidden ? null : animate);
    document.addEventListener("visibilitychange", updateVisibility);
    renderer.setAnimationLoop(animate);

    return () => {
      document.removeEventListener("visibilitychange", updateVisibility);
      resizeObserver.disconnect();
      renderer.setAnimationLoop(null);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
    };
  }, [animated]);

  const colors = STATUS_COLORS[status];
  const sizeValue = SIZE_MAP[size];

  return (
    <div className={`safety-gate-orb safety-gate-orb--${status.toLowerCase()} safety-gate-orb--${size}`}>
      <div className="safety-gate-orb__canvas-wrapper" style={{ width: sizeValue, height: sizeValue }}>
        {animated ? (
          <canvas ref={canvasRef} className="safety-gate-orb__canvas" aria-hidden="true" />
        ) : (
          <div className="safety-gate-orb__static" style={{ backgroundColor: colors.core }} />
        )}
      </div>
      <div className="safety-gate-orb__label">
        <strong>{colors.label}</strong>
      </div>
    </div>
  );
}
