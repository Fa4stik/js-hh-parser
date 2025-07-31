declare global {
  namespace NodeJS {
    interface ProcessEnv {
      API_HH_URL: string;
    }
  }
}

export {}