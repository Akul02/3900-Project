import ProfileHeader from "@/components/profileHeader"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import useUser from "@/hooks/useUser"
import { HTTPProfileService } from "@/service/profileService"
import { MessageCircle, User } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/router"
import { useQuery } from "react-query"

const profileService = new HTTPProfileService()
export default function StudentProfile() {
  const router = useRouter()
  const { user } = useUser()
  const studentId = router.query.studentId as string
  const isOwnProfile = studentId === user?.userId
  const { data } = useQuery({
    queryKey: ["students", studentId],
    queryFn: () => profileService.getStudentProfile(studentId),
  })
  if (!data) {
    return <div>loading</div>
  }
  return (
    <div className="h-full w-full p-12">
      <div className="mx-auto flex max-w-xl flex-col items-stretch gap-3">
        <ProfileHeader
          name={data.name}
          accountType="Student"
          email={data.email}
          profilePicture={data.profilePicture}
          phoneNumber={data.phoneNumber}
          location={data.location}
        />
        {isOwnProfile ? (
          <Button asChild variant="secondary" className="flex grow gap-2">
            <Link href={`${user?.userId}/edit`}>
              <User className="w-5" />
              Edit Profile
            </Link>
          </Button>
        ) : (
          <Button variant="secondary" className="flex grow gap-2">
            <MessageCircle className="w-5" />
            Message Student
          </Button>
        )}
        <Card className="mt-5">
          <CardHeader>
            <CardTitle>About me</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="whitespace-pre-wrap">{data.bio}</div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
