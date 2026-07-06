-- DropForeignKey
ALTER TABLE "ComplaintMessage" DROP CONSTRAINT "ComplaintMessage_complaintId_fkey";

-- DropForeignKey
ALTER TABLE "Submission" DROP CONSTRAINT "Submission_taskId_fkey";

-- AlterTable
ALTER TABLE "ComplaintMessage" ADD COLUMN     "senderName" TEXT NOT NULL DEFAULT 'User',
ADD COLUMN     "senderRole" TEXT NOT NULL DEFAULT 'student';

-- AlterTable
ALTER TABLE "Material" ALTER COLUMN "status" SET DEFAULT 'ready';

-- AlterTable
ALTER TABLE "Task" ADD COLUMN     "classSectionId" TEXT;

-- AlterTable
ALTER TABLE "User" ADD COLUMN     "classSectionId" TEXT,
ADD COLUMN     "section" TEXT;

-- CreateTable
CREATE TABLE "ClassSection" (
    "id" TEXT NOT NULL,
    "collegeId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "section" TEXT NOT NULL,
    "semester" INTEGER NOT NULL,
    "branch" TEXT NOT NULL,
    "year" INTEGER NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ClassSection_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "ClassSection" ADD CONSTRAINT "ClassSection_collegeId_fkey" FOREIGN KEY ("collegeId") REFERENCES "College"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "User" ADD CONSTRAINT "User_classSectionId_fkey" FOREIGN KEY ("classSectionId") REFERENCES "ClassSection"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Task" ADD CONSTRAINT "Task_classSectionId_fkey" FOREIGN KEY ("classSectionId") REFERENCES "ClassSection"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Submission" ADD CONSTRAINT "Submission_taskId_fkey" FOREIGN KEY ("taskId") REFERENCES "Task"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ComplaintMessage" ADD CONSTRAINT "ComplaintMessage_complaintId_fkey" FOREIGN KEY ("complaintId") REFERENCES "Complaint"("id") ON DELETE CASCADE ON UPDATE CASCADE;
