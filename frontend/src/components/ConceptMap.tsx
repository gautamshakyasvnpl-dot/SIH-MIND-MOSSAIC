import { useMemo } from "react";

type Node = { id: string; label: string };
type Edge = { from: string; to: string };

const BOX_W = 150;
const BOX_H = 52;
const GAP_X = 40;
const GAP_Y = 70;
const MAX_CHARS = 24;

function parseMermaid(src: string): { nodes: Node[]; edges: Edge[] } | null {
  const lines = src
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  if (!/^graph\s+(TD|TB|LR)?/i.test(lines[0] ?? "")) return null;

  const labels = new Map<string, string>();
  const edges: Edge[] = [];
  const edgeRe =
    /^([A-Za-z0-9_]+)\s*(?:-->|---|-->)\s*([A-Za-z0-9_]+)\s*(?:\||\||;|$)/;

  for (const line of lines.slice(1)) {
    const defMatch = line.match(/^([A-Za-z0-9_]+)\s*[[(]\s*["']?([^"'\])]*)["']?\s*[\])]/);
    if (defMatch) {
      const label = defMatch[2].trim() || defMatch[1];
      labels.set(defMatch[1], label);
      continue;
    }
    const edgeParts = line.split(/\s*(?:-->|---)\s*/);
    if (edgeParts.length === 2) {
      const clean = (raw: string) => raw.replace(/[|;]/g, "").trim();
      const left = clean(edgeParts[0]);
      const rightRaw = edgeParts[1].split("|")[0].trim();
      const rightDef = rightRaw.match(/^([A-Za-z0-9_]+)/);
      const right = rightDef ? rightDef[1] : clean(rightRaw);
      if (left && right && !edgeParts[0].includes('"')) {
        edges.push({ from: left, to: right });
        const rightLabelInEdge = rightRaw.match(/^[A-Za-z0-9_]+\[\s*["']?([^"'\]]*)["']?\s*\]/);
        if (rightLabelInEdge) labels.set(right, rightLabelInEdge[1].trim() || right);
      }
      void edgeRe;
    }
  }

  if (labels.size === 0) return null;
  const nodes: Node[] = [...labels.entries()].map(([id, label]) => ({ id, label }));
  return { nodes, edges };
}

function wrap(text: string): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let current = "";
  for (const w of words) {
    if ((current + " " + w).trim().length > MAX_CHARS && current) {
      lines.push(current.trim());
      current = w;
    } else {
      current = `${current} ${w}`;
    }
  }
  if (current.trim()) lines.push(current.trim());
  return lines.slice(0, 3);
}

export default function ConceptMap({ src }: { src: string }) {
  const layout = useMemo(() => {
    const parsed = parseMermaid(src);
    if (!parsed) return null;
    const { nodes, edges } = parsed;

    const incoming = new Map<string, number>();
    for (const n of nodes) incoming.set(n.id, 0);
    for (const e of edges) incoming.set(e.to, (incoming.get(e.to) ?? 0) + 1);

    const levelOf = new Map<string, number>();
    const roots = nodes.filter((n) => (incoming.get(n.id) ?? 0) === 0).map((n) => n.id);
    const queue = [...(roots.length ? roots : [nodes[0].id])];
    queue.forEach((id) => levelOf.set(id, 0));
    let guard = 0;
    while (queue.length && guard < 500) {
      guard += 1;
      const id = queue.shift() as string;
      const lvl = levelOf.get(id) ?? 0;
      for (const e of edges.filter((x) => x.from === id)) {
        if (!levelOf.has(e.to)) {
          levelOf.set(e.to, lvl + 1);
          queue.push(e.to);
        }
      }
    }

    const byLevel = new Map<number, Node[]>();
    for (const n of nodes) {
      const lvl = levelOf.get(n.id) ?? 0;
      if (!byLevel.has(lvl)) byLevel.set(lvl, []);
      byLevel.get(lvl)?.push(n);
    }
    const levels = [...byLevel.keys()].sort((a, b) => a - b);
    const pos = new Map<string, { x: number; y: number }>();
    let maxCols = 0;
    levels.forEach((lvl, rowIdx) => {
      const row = byLevel.get(lvl) ?? [];
      maxCols = Math.max(maxCols, row.length);
      row.forEach((n, colIdx) => {
        pos.set(n.id, {
          x: colIdx * (BOX_W + GAP_X),
          y: rowIdx * (BOX_H + GAP_Y),
        });
      });
    });

    const width = Math.max(maxCols * (BOX_W + GAP_X) - GAP_X, BOX_W);
    const height = levels.length * (BOX_H + GAP_Y) - GAP_Y;
    return { nodes, edges, pos, width, height };
  }, [src]);

  if (!layout) {
    return (
      <pre style={{ whiteSpace: "pre-wrap", overflowX: "auto" }}>
        <code>{src}</code>
      </pre>
    );
  }

  const { nodes, edges, pos, width, height } = layout;

  return (
    <figure>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        width="100%"
        role="img"
        aria-label={`Concept map with ${nodes.length} ideas connected by ${edges.length} links`}
        style={{ maxWidth: width, height: "auto" }}
      >
        <defs>
          <marker
            id="cm-arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#5b5344" />
          </marker>
        </defs>
        {edges.map((e) => {
          const a = pos.get(e.from);
          const b = pos.get(e.to);
          if (!a || !b) return null;
          return (
            <line
              key={`${e.from}-${e.to}`}
              x1={a.x + BOX_W / 2}
              y1={a.y + BOX_H}
              x2={b.x + BOX_W / 2}
              y2={b.y}
              stroke="#5b5344"
              strokeWidth="2"
              markerEnd="url(#cm-arrow)"
            />
          );
        })}
        {nodes.map((n) => {
          const p = pos.get(n.id);
          if (!p) return null;
          const lines = wrap(n.label);
          const firstY = p.y + BOX_H / 2 - ((lines.length - 1) * 15) / 2 + 4;
          return (
            <g key={n.id}>
              <rect
                x={p.x}
                y={p.y}
                width={BOX_W}
                height={BOX_H}
                rx="12"
                fill="#fffdf7"
                stroke={lines.length ? "#9c4a1f" : "#e4d8c2"}
                strokeWidth="2"
              />
              {lines.map((ln, i) => (
                <text
                  key={i}
                  x={p.x + BOX_W / 2}
                  y={firstY + i * 15}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#29241c"
                >
                  {ln}
                </text>
              ))}
            </g>
          );
        })}
      </svg>
      <details>
        <summary>View diagram as text (Mermaid)</summary>
        <pre style={{ whiteSpace: "pre-wrap" }}>
          <code>{src}</code>
        </pre>
      </details>
      <figcaption className="visually-hidden-note" style={{ display: "none" }}>
        {nodes.map((n) => n.label).join("; ")}
      </figcaption>
    </figure>
  );
}
