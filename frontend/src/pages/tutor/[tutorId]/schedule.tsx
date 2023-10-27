import EditAppointmentForm from "@/components/editAppointmentForm"
import SmartAvatar from "@/components/smartAvatar"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
} from "@/components/ui/dialog"
import WeeklyCalendar from "@/components/weeklyCalendar"
import useUser from "@/hooks/useUser"
import { cn } from "@/lib/utils"
import { MockAppointmentService } from "@/service/appointmentService"
import { HTTPProfileService } from "@/service/profileService"
import { addHours } from "date-fns"
import Link from "next/link"
import { useRouter } from "next/router"
import { useState } from "react"
import { useQuery, useQueryClient } from "react-query"

const profileService = new HTTPProfileService()
export default function Schedule() {
  const queryClient = useQueryClient()
  const { user } = useUser()
  const [appointmentService] = useState(
    new MockAppointmentService(user?.userId || ""),
  )
  const router = useRouter()
  const tutorId = router.query.tutorId as string
  const isOwnSchedule = user?.userId == tutorId
  const [creatingAppointment, setCreatingAppointment] = useState(false)
  const [clickedStartTime, setClickedStartTime] = useState<undefined | Date>()

  const { data: scheduleData } = useQuery({
    queryKey: ["tutors", tutorId, "schedule"],
    queryFn: async () => {
      let { timesAvailable } = await profileService.getTutorProfile(tutorId)
      timesAvailable = [
        ...timesAvailable,
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
      ]
      return timesAvailable.map((ta) => ({
        start: new Date(ta.startTime),
        end: new Date(ta.endTime),
      }))
    },
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  })

  const { data: profileData } = useQuery({
    queryKey: ["tutors", tutorId],
    queryFn: async () => {
      const tutorProfile = await profileService.getTutorProfile(tutorId)
      return tutorProfile
    },
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
  })

  const { data: appointmentData } = useQuery({
    queryKey: ["tutors", tutorId, "appointments"],
    queryFn: () => appointmentService.getTutorAppointments(tutorId),
  })

  return (
    <div className="relative flex h-full w-full flex-col gap-10 overflow-hidden p-10">
      <div className="flex gap-4">
        <Link href={`/tutor/${tutorId}`}>
          <SmartAvatar
            className="h-16 w-16 text-3xl"
            loading={!profileData}
            name={profileData?.name}
            profilePicture={profileData?.profilePicture}
          />
        </Link>

        <h1 className="flex items-center text-xl ">
          <Link href={`/tutor/${tutorId}`} className="hover:underline">
            {profileData?.name}
          </Link>
          &apos;s&nbsp;Schedule
        </h1>
      </div>
      <WeeklyCalendar
        onCalendarClick={(clickedDate) => {
          setCreatingAppointment(true)
          setClickedStartTime(clickedDate)
        }}
        interactiveIntervals={[
          ...(appointmentData?.yourAppointments.map((appointment) => ({
            interval: {
              start: appointment.startTime,
              end: appointment.endTime,
            },
            title: `${
              appointment.tutorAccepted ? "Appointment" : "Requested"
            } with Daniel Nguyen`,
            componentProps: {
              className: cn(
                "bg-green-300/40 border border-green-500",
                !appointment.tutorAccepted &&
                  "bg-slate-300/40 border-dashed border-slate-500",
              ),
              onClick: (e: React.SyntheticEvent) => {
                e.stopPropagation()
              },
            },
          })) || []),
          ...(scheduleData?.map((interval) => ({
            interval,
            componentProps: {
              className: "bg-white -z-10 text-white/0",
            },
          })) || []),
        ]}
      />
      <Dialog
        open={creatingAppointment}
        onOpenChange={(open) => setCreatingAppointment(open)}
      >
        <DialogContent className="fade-in-0">
          <DialogHeader>
            Requesting appointment with {profileData?.name}
          </DialogHeader>
          <DialogDescription asChild>
            <EditAppointmentForm
              startTime={clickedStartTime}
              submitFn={async (start, end) => {
                await new Promise((resolve) => setTimeout(resolve, 1000))
                // toast(start.toString() + end.toString())
                await appointmentService.requestAppointment(tutorId, start, end)
                setCreatingAppointment(false)
                queryClient.invalidateQueries({
                  queryKey: ["tutors", tutorId, "appointments"],
                })
                return true
              }}
              cancelFn={() => setCreatingAppointment(false)}
            />
          </DialogDescription>
        </DialogContent>
      </Dialog>
    </div>
  )
}
