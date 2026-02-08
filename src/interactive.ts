import { query, type Options } from "@anthropic-ai/claude-agent-sdk";
import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { createInterface } from "readline";

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectDir = resolve(__dirname, "..");

function loadEnv() {
  try {
    const envPath = resolve(projectDir, ".env");
    const content = readFileSync(envPath, "utf-8");
    for (const line of content.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const eqIndex = trimmed.indexOf("=");
      if (eqIndex === -1) continue;
      const key = trimmed.slice(0, eqIndex).trim();
      const value = trimmed.slice(eqIndex + 1).trim();
      if (!process.env[key]) {
        process.env[key] = value;
      }
    }
  } catch {
    // .env file is optional
  }
}

loadEnv();

const API_KEY = process.env.ICEPANEL_API_KEY;
const ORGANIZATION_ID = process.env.ICEPANEL_ORGANIZATION_ID;

// IcePanel MCP server is optional — only included when credentials are available
const mcpServers: Record<string, any> = {};
const allowedTools = [
  "Skill",
  "Bash",
  "Read",
  "Write",
  "Glob",
  "Grep",
];

if (API_KEY && ORGANIZATION_ID) {
  mcpServers.icepanel = {
    command: "npx",
    args: ["-y", "@icepanel/mcp-server@latest"],
    env: {
      API_KEY,
      ORGANIZATION_ID,
    },
  };
  allowedTools.push("mcp__icepanel__*");
  console.log("IcePanel mode available (credentials found)");
} else {
  console.log(
    "IcePanel credentials not found — only Mermaid mode is available."
  );
  console.log(
    "To enable IcePanel mode, set ICEPANEL_API_KEY and ICEPANEL_ORGANIZATION_ID in .env"
  );
}

const rl = createInterface({
  input: process.stdin,
  output: process.stdout,
});

function ask(question: string): Promise<string> {
  return new Promise((resolve) => rl.question(question, resolve));
}

console.log("Architecture Diagram Agent - Interactive Mode");
console.log('Type your request, or "quit" to exit.\n');

while (true) {
  const userPrompt = await ask("You: ");

  if (userPrompt.trim().toLowerCase() === "quit") {
    console.log("Goodbye!");
    rl.close();
    break;
  }

  if (!userPrompt.trim()) continue;

  const abort = new AbortController();
  process.on("SIGINT", () => abort.abort());

  const options: Options = {
    cwd: projectDir,
    settingSources: ["user", "project"],
    mcpServers,
    allowedTools,
    maxTurns: 25,
    abortController: abort,
  };

  console.log("\nAgent:");

  for await (const message of query({ prompt: userPrompt, options })) {
    if (message.type === "assistant") {
      for (const block of message.message?.content ?? []) {
        if (block.type === "text") {
          console.log((block as { text: string }).text);
        }
        if (block.type === "tool_use") {
          const tool = block as { name: string };
          console.log(`  [Tool: ${tool.name}]`);
        }
      }
    }

    if (message.type === "result") {
      if (message.subtype !== "success") {
        console.error(`Failed: ${message.subtype}`, message.errors);
      }
    }
  }

  console.log();
}
