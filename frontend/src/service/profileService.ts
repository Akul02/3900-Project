import TutorProfile from "@/pages/tutor/[tutorId]"
import wretch from "wretch"
import { SuccessResponse } from "./types"
import { HTTPService } from "./helpers"
import { addHours } from "date-fns"

interface UserProfile {
  id: string
  name: string
  bio: string
  email: string
  profilePicture: string | null
  location: string | null
  phoneNumber: string | null
}

export interface TutorProfile extends UserProfile {
  courseOfferings: string[]
  timesAvailable: {
    startTime: string
    endTime: string
  }[]
}

export interface StudentProfile extends UserProfile {}
export interface TutorSelfEditReqBody extends Omit<TutorProfile, "id"> {}
export interface StudentSelfEditReqBody extends Omit<StudentProfile, "id"> {}

/**
 * ProfileService provides operations relating to tutor/student profiles
 */
export interface TutorSearchParams {
  name?: string
  location?: string
  rating?: string
  courseOfferings?: string[]
  timeRange?: {
    startTime: string
    endTime: string
  }
}
export interface ProfileService {
  getTutorProfile: (tutorId: string) => Promise<TutorProfile>
  setOwnTutorProfile: (
    tutorProfile: TutorSelfEditReqBody,
  ) => Promise<SuccessResponse>
  searchTutors: (
    searchParams: TutorSearchParams,
  ) => Promise<{ tutorIds: string[] }>
  getStudentProfile: (studentId: string) => Promise<StudentProfile>
  setOwnStudentProfile: (
    studentProfile: StudentSelfEditReqBody,
  ) => Promise<SuccessResponse>
}

export class HTTPProfileService extends HTTPService implements ProfileService {
  async searchTutors(
    searchParams: TutorSearchParams,
  ): Promise<{ tutorIds: string[] }> {
    const url = new URL(`${this.backendURL}/searchtutor`)
    const basicParams = { ...searchParams }
    delete basicParams.courseOfferings
    delete basicParams.timeRange
    const params = new URLSearchParams(basicParams as Record<string, string>)
    if (searchParams.timeRange) {
      params.set("timeRange", JSON.stringify(searchParams.timeRange))
    }
    if (searchParams.courseOfferings) {
      params.set(
        "courseOfferings",
        JSON.stringify(searchParams.courseOfferings),
      )
    }
    url.search = params.toString()
    const data = wretch(url.toString()).get()
    return await data.json()
  }
  async getTutorProfile(tutorId: string): Promise<TutorProfile> {
    const resp = wretch(`${this.backendURL}/tutor/${tutorId}`)
      .options({
        credentials: "include",
        mode: "cors",
      })
      .get()
    return await resp.json()
  }

  async setOwnTutorProfile(
    tutorProfile: TutorSelfEditReqBody,
  ): Promise<SuccessResponse> {
    const resp = wretch(`${this.backendURL}/tutor/profile`)
      .options({
        credentials: "include",
        mode: "cors",
      })
      .json(tutorProfile)
      .put()
    return resp.json()
  }

  async deleteOwnTutorProfile(tutorId: string): Promise<SuccessResponse> {
    const resp = wretch(`${this.backendURL}/tutor/`)
      .options({
        credentials: "include",
        mode: "cors",
      })
      .json({})
      .delete()
    return await resp.json()
  }

  async getStudentProfile(studentId: string): Promise<StudentProfile> {
    const resp = wretch(`${this.backendURL}/student/${studentId}`)
      .options({
        credentials: "include",
        mode: "cors",
      })
      .get()
    return await resp.json()
  }

  async setOwnStudentProfile(
    studentProfile: StudentSelfEditReqBody,
  ): Promise<SuccessResponse> {
    const resp = wretch(`${this.backendURL}/student/profile`)
      .options({
        credentials: "include",
        mode: "cors",
      })
      .json(studentProfile)
      .put()
    return resp.json()
  }
  async deleteOwnStudentProfile(studentId: string): Promise<SuccessResponse> {
    const resp = wretch(`${this.backendURL}/student/`)
      .options({
        credentials: "include",
        mode: "cors",
      })
      .json({})
      .delete()
    return await resp.json()
  }
}

export class MockProfileService implements ProfileService {
  private mockTutorProfile: TutorProfile = {
    id: "1337",
    name: "Daniel Nguyen",
    bio: "I tutor Computer Science at UNSW and I like grape gummy candy. It is a pleasure to meet you.",
    email: "daniel.nguyen.s173@gmail.com",
    profilePicture: null,
    location: "Sydney",
    phoneNumber: "0411111111",
    courseOfferings: ["COMP2041", "COMP6080"],
    timesAvailable: [
      {
        startTime: addHours(new Date(), 24).toISOString(),
        endTime: addHours(new Date(), 25).toISOString(),
      },
      {
        startTime: addHours(new Date(), 48).toISOString(),
        endTime: addHours(new Date(), 54).toISOString(),
      },
      {
        startTime: addHours(new Date(), 32).toISOString(),
        endTime: addHours(new Date(), 38).toISOString(),
      },
    ],
  }

  private mockStudentProfile: StudentProfile = {
    id: "64",
    name: "Daniel Wang",
    bio: "I need help with COMP6080",
    email: "daniel.wang@gmail.com",
    profilePicture: null,
    location: "Sydney",
    phoneNumber: "0499999999",
  }
  async getTutorProfile(_tutorId: string) {
    return this.mockTutorProfile
  }

  async setOwnTutorProfile(tutorProfile: TutorSelfEditReqBody) {
    this.mockTutorProfile = { ...tutorProfile, id: "1337" }
    return { success: true }
  }

  async deleteOwnTutorProfile(tutorId: string) {
    return { success: true }
  }

  async searchTutors(_searchParams: TutorSearchParams) {
    return { tutorIds: ["1337"] }
  }

  async getStudentProfile(_studentId: string) {
    return this.mockStudentProfile
  }

  async setOwnStudentProfile(studentProfile: StudentSelfEditReqBody) {
    this.mockStudentProfile = {
      ...studentProfile,
      id: this.mockStudentProfile.id,
    }
    return { success: true }
  }
}
