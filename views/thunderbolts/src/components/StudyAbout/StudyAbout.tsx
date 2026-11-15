import { useLayoutEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Box, Typography } from "@mui/material";
import "./StudyAbout.scss";

export type AboutSection = { key: string; label: string; text: string };

type Block =
  | { type: "p"; text: string }
  | { type: "ol"; items: string[] }
  | { type: "kv"; items: { label: string; text: string }[] };

const STEP = /^\(?(\d{1,2})[.)]\s+(.+)$/;
const LABELED = /^([A-Z][A-Za-z/&-]*(?: [A-Za-z/&-]+){0,3}):\s+(.+)$/;
const COLLAPSED_HEIGHT = 260;

// Quebra parágrafos muito longos em blocos de 2 a 3 frases.
function chunkParagraph(text: string): string[] {
  if (text.length < 420) return [text];
  const sentences = text.split(/(?<=[.!?])\s+(?=[A-Z(])/);
  const out: string[] = [];
  let current = "";
  for (const sentence of sentences) {
    if (current && `${current} ${sentence}`.length > 380) {
      out.push(current);
      current = sentence;
    } else {
      current = current ? `${current} ${sentence}` : sentence;
    }
  }
  if (current) out.push(current);
  return out;
}

// Transforma o texto bruto em parágrafos, passos numerados e itens "Rótulo: texto".
function parseText(raw: string): Block[] {
  const lines = raw
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  const blocks: Block[] = [];

  for (const line of lines) {
    const last = blocks[blocks.length - 1];

    const step = line.match(STEP);
    if (step) {
      if (last?.type === "ol") last.items.push(step[2]);
      else blocks.push({ type: "ol", items: [step[2]] });
      continue;
    }

    const kv = line.match(LABELED);
    if (kv) {
      const item = { label: kv[1], text: kv[2] };
      if (last?.type === "kv") last.items.push(item);
      else blocks.push({ type: "kv", items: [item] });
      continue;
    }

    for (const chunk of chunkParagraph(line)) blocks.push({ type: "p", text: chunk });
  }
  return blocks;
}

function Collapsible({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const [overflowing, setOverflowing] = useState(false);
  const [open, setOpen] = useState(false);

  useLayoutEffect(() => {
    const el = ref.current;
    if (el) setOverflowing(el.scrollHeight > COLLAPSED_HEIGHT + 40);
  }, []);

  const clamped = overflowing && !open;

  return (
    <>
      <Box
        component={"div"}
        ref={ref}
        className={`about__body${clamped ? " about__body--clamped" : ""}`}
      >
        {children}
      </Box>
      {overflowing && (
        <button type="button" className="about__toggle" onClick={() => setOpen((v) => !v)}>
          {open ? "Show less ↑" : "Show more ↓"}
        </button>
      )}
    </>
  );
}

function renderBlock(block: Block, i: number) {
  if (block.type === "p") {
    return (
      <Typography key={i} className="about__p">
        {block.text}
      </Typography>
    );
  }
  if (block.type === "ol") {
    return (
      <ol key={i} className="about__steps">
        {block.items.map((item, j) => (
          <li key={j}>
            <span>{item}</span>
          </li>
        ))}
      </ol>
    );
  }
  return (
    <Box component={"div"} key={i} className="about__callouts">
      {block.items.map((item) => (
        <Box component={"div"} key={item.label} className="about__callout">
          <Typography className="about__callout-label">{item.label}</Typography>
          <Typography className="about__callout-text">{item.text}</Typography>
        </Box>
      ))}
    </Box>
  );
}

export default function StudyAbout({ sections }: { sections: AboutSection[] }) {
  const available = sections.filter((s) => s.text.trim());
  const [active, setActive] = useState(available[0]?.key ?? "");

  if (available.length === 0) return null;

  const current = available.find((s) => s.key === active) ?? available[0];
  const blocks = parseText(current.text);

  return (
    <Box component={"div"} className="about-root">
      <Box component={"div"} className="about__tabs" role="tablist">
        {available.map((s) => (
          <button
            key={s.key}
            type="button"
            role="tab"
            aria-selected={s.key === current.key}
            className={`about__tab${s.key === current.key ? " about__tab--active" : ""}`}
            onClick={() => setActive(s.key)}
          >
            {s.label}
          </button>
        ))}
      </Box>

      <Box component={"div"} className="about__panel" role="tabpanel" key={current.key}>
        <Collapsible>{blocks.map(renderBlock)}</Collapsible>
      </Box>
    </Box>
  );
}