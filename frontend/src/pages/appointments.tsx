import WeeklyCalendar from "@/components/weeklyCalendar"
import useUser from "@/hooks/useUser"
import { MockProfileService } from "@/service/profileService"
import { useQuery } from "react-query"

const profileService = new MockProfileService()
export default function Appointments() {
  const { user } = useUser()
  const { data } = useQuery({
    queryKey: ["tutors", user?.userId as string, "timeAvailable"],
    queryFn: async () => {
      const { timesAvailable } = await profileService.getTutorProfile(
        user?.userId as string,
      )
      return timesAvailable.map((ta) => ({
        start: new Date(ta.startTime),
        end: new Date(ta.endTime),
      }))
    },
  })
  return (
    <div className="relative h-full w-full overflow-hidden p-16">
      <WeeklyCalendar interactiveIntervals={[]} />
    </div>
  )
}
