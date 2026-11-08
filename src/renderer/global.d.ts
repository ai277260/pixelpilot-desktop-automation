interface Window { automator: { command: (command: Record<string, unknown>) => Promise<{ok:boolean}>; chooseTemplate: () => Promise<string | null>; loadConfig: () => Promise<{steps?: unknown[]; loop?: boolean} | null>; saveConfig: (config: unknown) => Promise<{ok:boolean}>; onEvent: (callback: (event: Record<string, unknown>) => void) => () => void } }

