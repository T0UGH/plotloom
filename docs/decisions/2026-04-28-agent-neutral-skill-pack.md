---
title: Plotloom 方向修正：Agent-neutral Skill Pack
created: 2026-04-28
agent: nova
material_type: decision-note
status: raw
tags:
  - plotloom
  - agent-neutral
  - skills
  - codex
  - claude-code
  - openclaw
  - hermes
---

# Plotloom 方向修正：Agent-neutral Skill Pack

## 结论

Plotloom 不做只绑定 Claude Code 的 skills。

Plotloom 应该是一组 **agent-neutral skills**：核心能力以中立协议、artifact contract、模板、references、scripts 的方式组织，让 Codex、Claude Code、OpenClaw、Hermes 等 agent 都能快速接入。

## 设计约束

- 核心工作流不依赖单一 agent runtime。
- skill 内容应能被不同 agent 以 adaptor 方式加载。
- artifact contract 独立于 agent：例如 `episode.yaml`、`characters.yaml`、`shots.yaml`、`assets.yaml`、`manifest.json`。
- 每个 agent adaptor 只解决：发现 skill、加载上下文、执行脚本、写回 artifact。
- 第一阶段先研究规范，不急于写重 CLI 或平台。

## 下一步调研顺序

1. 跨 agent skill / plugin / instruction 接入形态。
2. Plotloom 中立 skill manifest。
3. Plotloom MVP artifact contract。
4. agent adaptor 设计：Codex / Claude Code / OpenClaw / Hermes。
5. 45 秒短剧端到端 MVP 的最小 skill 集合。
