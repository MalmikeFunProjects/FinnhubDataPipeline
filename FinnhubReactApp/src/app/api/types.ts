import { NextRequest } from 'next/server';

export interface ExtendedNextRequest extends NextRequest {
  user?: {
    id: string;
    role: string;
  };
}

export type ApiHandler<T = any> = (
  req: ExtendedNextRequest
) => Promise<Response> | Response;
