import { z } from "zod";
import { IdNamedSchema } from "./common";

export const IndustryResponse = z.object({
  id: z.string(),
  name: z.string(),
  industries: z.array(IdNamedSchema),
});
export type IndustryResponse = z.infer<typeof IndustryResponse>