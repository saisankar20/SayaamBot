import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
/// <reference types="vite/client" />
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(process.cwd(), "src"),   // enables "@/..." imports
    },
  },
});
