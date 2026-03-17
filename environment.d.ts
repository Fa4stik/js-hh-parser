declare global {
  namespace NodeJS {
    interface ProcessEnv {
      API_HH_URL: string;
      IS_PROXY: '1' | '',
      THREADS: `${number}`
    }
  }
}

export {}