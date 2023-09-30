import wretch from "wretch"
import { WretchError } from "wretch/resolver"

export interface RegisterBody {
  name: string
  email: string
  password: string
  accountType: "admin" | "tutor" | "student"
}

export class HTTPAuthService {
  private backendURL: string
  private errorHandlerCallback = async (resp: WretchError) => {
    const error = await resp.json()
    throw new Error(error.error)
  }
  constructor() {
    this.backendURL = process.env.BACKEND_URL || "http://127.0.0.1:5000"
  }
  async register(registerBody: RegisterBody) {
    const resp = wretch(`${this.backendURL}/register`)
      .json(registerBody)
      .post()
      .badRequest(this.errorHandlerCallback)
      .error(415, this.errorHandlerCallback)
    const data = resp.json()
    console.log(data)
    return data
  }
}