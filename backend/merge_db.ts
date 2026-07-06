import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()

async function main() {
  console.log('Starting database merge...')

  // Get the first/main college
  const colleges = await prisma.college.findMany({ orderBy: { createdAt: 'asc' } })
  console.log('Found colleges:', colleges.map(c => c.id + ' - ' + c.domain))

  if (colleges.length <= 1) {
    console.log('Only one college - no merge needed!')
    return
  }

  const mainCollege = colleges[0]
  const otherIds = colleges.slice(1).map(c => c.id)

  console.log('Main college:', mainCollege.id, mainCollege.domain)
  console.log('Merging colleges:', otherIds)

  // Move all data to main college
  await prisma.user.updateMany({ where: { collegeId: { in: otherIds } }, data: { collegeId: mainCollege.id } })
  await prisma.classSection.updateMany({ where: { collegeId: { in: otherIds } }, data: { collegeId: mainCollege.id } })
  await prisma.task.updateMany({ where: { collegeId: { in: otherIds } }, data: { collegeId: mainCollege.id } })
  await prisma.material.updateMany({ where: { collegeId: { in: otherIds } }, data: { collegeId: mainCollege.id } })

  // Delete other colleges
  await prisma.college.deleteMany({ where: { id: { in: otherIds } } })

  console.log('DONE! All data merged into single college:', mainCollege.id)
  const counts = {
    users: await prisma.user.count({ where: { collegeId: mainCollege.id } }),
    classes: await prisma.classSection.count({ where: { collegeId: mainCollege.id } }),
    tasks: await prisma.task.count({ where: { collegeId: mainCollege.id } }),
    materials: await prisma.material.count({ where: { collegeId: mainCollege.id } }),
  }
  console.log('Data counts:', counts)
}

main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1) })
