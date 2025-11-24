type Props = {
  visible: boolean;
  gridColor: string;
  backgroundColor: string;
  spacing: number;
  thickness: number;
  onChange: (partial: Partial<{
    visible: boolean;
    gridColor: string;
    backgroundColor: string;
    spacing: number;
    thickness: number;
  }>) => void;
  onApply: () => Promise<void> | void;
};

export function GridControls({
  visible,
  gridColor,
  backgroundColor,
  spacing,
  thickness,
  onChange,
  onApply,
}: Props) {
  return (
    <section style={{ border: "1px solid #cbd5f5", borderRadius: 8, padding: 16, background: "#fff" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>Grid & Background</h3>
        <label style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          <input
            type="checkbox"
            checked={visible}
            onChange={() => onChange({ visible: !visible })}
          />
          Show grid
        </label>
      </header>
      <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
        <label style={{ display: "block" }}>
          Grid color
          <input
            type="color"
            value={gridColor}
            onChange={(event) => onChange({ gridColor: event.target.value })}
            style={{ marginLeft: 12, verticalAlign: "middle" }}
          />
        </label>
        <label style={{ display: "block" }}>
          Background color
          <input
            type="color"
            value={backgroundColor}
            onChange={(event) => onChange({ backgroundColor: event.target.value })}
            style={{ marginLeft: 12, verticalAlign: "middle" }}
          />
        </label>
        <label style={{ display: "block" }}>
          Grid spacing (px)
          <input
            type="number"
            min={10}
            max={400}
            value={spacing}
            onChange={(event) => onChange({ spacing: Number(event.target.value) || 10 })}
            style={{ width: "100%", marginTop: 4 }}
          />
        </label>
        <label style={{ display: "block" }}>
          Line thickness (px)
          <input
            type="number"
            min={0.5}
            max={10}
            step={0.5}
            value={thickness}
            onChange={(event) => onChange({ thickness: Number(event.target.value) || 1 })}
            style={{ width: "100%", marginTop: 4 }}
          />
        </label>
        <button
          type="button"
          onClick={() => onApply()}
          style={{
            marginTop: 8,
            padding: "8px 12px",
            borderRadius: 6,
            border: "none",
            background: "#2563eb",
            color: "#fff",
          }}
        >
          Apply Grid Settings
        </button>
      </div>
    </section>
  );
}


