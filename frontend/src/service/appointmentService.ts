import { addHours, addWeeks } from "date-fns"
import { nanoid } from "nanoid"

interface AppointmentResp {
  id: string
  startTime: Date
  endTime: Date
  studentId?: string // undefined if no access to appointment
  tutorId: string
  tutorAccepted: boolean
}

interface TutorAppointmentsResp {
  yourAppointments: AppointmentResp[]
  other: AppointmentResp[]
}

interface AppointmentService {
  requestAppointment: (
    tutorId: string,
    start: Date,
    end: Date,
  ) => Promise<AppointmentResp>
  getTutorAppointments: (tutorId: string) => Promise<TutorAppointmentsResp>
}

export class MockAppointmentService implements AppointmentService {
  private yourAppointments: AppointmentResp[] = []
  private userId: string
  constructor(userId: string) {
    this.userId = userId
  }
  private generateMockAppointment(
    tutorId: string | undefined,
    startTime: Date | undefined,
    endTime: Date | undefined,
  ): AppointmentResp {
    const newAppointment = {
      id: nanoid(),
      startTime: startTime ? startTime : new Date(),
      endTime: endTime ? endTime : addHours(new Date(), 1),
      studentId: this.userId,
      tutorId: tutorId ? tutorId : nanoid(),
      tutorAccepted: Math.random() > 0.5,
    }
    this.yourAppointments.push(newAppointment)
    return newAppointment
  }
  async requestAppointment(tutorId: string, start: Date, end: Date) {
    return this.generateMockAppointment(tutorId, start, end)
  }

  async getTutorAppointments(_tutorId: string) {
    return {
      yourAppointments: this.yourAppointments,
      other: this.yourAppointments.map((appointment) => {
        const other = {
          ...appointment,
          startTime: addWeeks(appointment.startTime, 2),
          endTime: addWeeks(appointment.endTime, 2),
        }
        delete other.studentId
        return other
      }),
    }
  }
}
