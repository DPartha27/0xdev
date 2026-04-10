"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { Header } from "@/components/layout/header";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useCourses, useSchools, Course as ApiCourse } from "@/lib/api";
import CourseCard from "@/components/CourseCard";
import CreateCourseDialog from "@/components/CreateCourseDialog";
import { Globe } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { data: session } = useSession();
  const { courses, isLoading, error } = useCourses();
  const { schools } = useSchools();
  const [isCreateCourseDialogOpen, setIsCreateCourseDialogOpen] = useState(false);

  useEffect(() => {
    document.title = 'Home · SensAI';
  }, []);

  // Memoize derived data to avoid recalculations
  const {
    teachingCourses,
    mentoringCourses,
    learningCourses,
    hasTeachingCourses,
    hasMentoringCourses,
    hasLearningCourses,
    hasAnyCourses,
    showSegmentedTabs,
    tabsToShow
  } = useMemo(() => {
    const teachingCourses = courses.filter(course => course.role === 'admin');
    const mentoringCourses = courses.filter(course => course.role === 'mentor');
    const learningCourses = courses.filter(course => course.role !== 'admin' && course.role !== 'mentor');
    const hasTeachingCourses = teachingCourses.length > 0;
    const hasMentoringCourses = mentoringCourses.length > 0;
    const hasLearningCourses = learningCourses.length > 0;

    const roleCount = [hasTeachingCourses, hasMentoringCourses, hasLearningCourses].filter(Boolean).length;
    const showSegmentedTabs = roleCount > 1;

    // Determine which tabs to show based on available roles
    const tabsToShow = [];
    if (hasTeachingCourses) tabsToShow.push('teaching');
    if (hasMentoringCourses) tabsToShow.push('mentoring');
    if (hasLearningCourses) tabsToShow.push('learning');

    return {
      teachingCourses,
      mentoringCourses,
      learningCourses,
      hasTeachingCourses,
      hasMentoringCourses,
      hasLearningCourses,
      hasAnyCourses: hasTeachingCourses || hasMentoringCourses || hasLearningCourses,
      showSegmentedTabs,
      tabsToShow
    };
  }, [courses]);

  // Memoize initialActiveTab calculation
  const initialActiveTab = useMemo(() => {
    if (hasLearningCourses && !hasTeachingCourses && !hasMentoringCourses) return 'learning';
    if (hasMentoringCourses && !hasTeachingCourses && !hasLearningCourses) return 'mentoring';
    if (hasTeachingCourses) return 'teaching';
    if (hasMentoringCourses) return 'mentoring';
    return 'learning';
  }, [hasLearningCourses, hasTeachingCourses, hasMentoringCourses]);

  const [activeTab, setActiveTab] = useState<'teaching' | 'mentoring' | 'learning'>(initialActiveTab);
  const [hasSchool, setHasSchool] = useState<boolean | null>(null);
  const [schoolId, setSchoolId] = useState<string | null>(null);

  // Update school state based on API data
  useEffect(() => {
    if (schools && schools.length > 0) {
      setHasSchool(true);
      setSchoolId(schools[0].id);
    } else {
      setHasSchool(false);
    }
  }, [schools]);

  // Handle tab changes only when related data changes
  useEffect(() => {
    // If current tab is no longer available, switch to first available tab
    if (!tabsToShow.includes(activeTab) && tabsToShow.length > 0) {
      setActiveTab(tabsToShow[0] as 'teaching' | 'mentoring' | 'learning');
    }
  }, [tabsToShow, activeTab]);

  // Memoize event handlers
  const handleCreateCourseButtonClick = useCallback(() => {
    if (hasSchool && schoolId) {
      // If school already exists, show the course creation dialog
      setIsCreateCourseDialogOpen(true);
    } else {
      // If no school exists, redirect to school creation page
      router.push("/school/admin/create");
    }
  }, [hasSchool, schoolId, router]);

  // Handle success callback from CreateCourseDialog
  const handleCourseCreationSuccess = useCallback((courseData: { id: string; name: string }) => {
    if (hasSchool && schoolId) {
      // Redirect to the new course page - dialog will be unmounted during navigation
      router.push(`/school/admin/${schoolId}/courses/${courseData.id}`);
    } else {
      router.push("/school/admin/create");
    }
  }, [hasSchool, schoolId, router]);

  // Get current tab's courses
  const getCurrentTabCourses = () => {
    switch (activeTab) {
      case 'teaching':
        return teachingCourses;
      case 'mentoring':
        return mentoringCourses;
      case 'learning':
        return learningCourses;
      default:
        return [];
    }
  };

  // Get title for single role scenario
  const getSingleRoleTitle = () => {
    if (hasMentoringCourses && !hasTeachingCourses && !hasLearningCourses) {
      return "Courses you are mentoring";
    }
    return "Your courses";
  };

  return (
    <>
      <style jsx global>{`
        button:focus {
          outline: none !important;
          box-shadow: none !important;
          border: none !important;
        }
        
        html, body {
          height: 100%;
          overflow-y: auto;
        }
      `}
      </style>

      <div className="min-h-screen overflow-y-auto bg-white dark:bg-black text-black dark:text-white">
        {/* Use the reusable Header component */}
        <Header
          showCreateCourseButton={hasAnyCourses || (hasSchool ?? false)}
          showTryDemoButton={!hasLearningCourses}
        />

        {/* Main content */}
        <main className="max-w-6xl mx-auto pt-6 px-8 pb-12">
          {/* Loading state */}
          {isLoading && (
            <div className="flex justify-center items-center py-12">
              <div className="w-12 h-12 border-t-2 border-b-2 rounded-full animate-spin border-foreground"></div>
            </div>
          )}

          {/* Content when loaded */}
          {!isLoading && (
            <>
              {/* Segmented control for tabs */}
              {showSegmentedTabs && (
                <div className="flex justify-center mb-8">
                  <div className="inline-flex rounded-lg p-1 w-full sm:w-auto bg-[#e5e7eb] dark:bg-[#222222]">
                    {tabsToShow.includes('teaching') && (
                      <button
                        className={`flex items-center justify-center px-1 xxs:px-2 sm:px-4 py-2 rounded-md text-xs sm:text-sm xxs:font-medium cursor-pointer flex-1 sm:flex-initial ${activeTab === 'teaching'
                          ? 'bg-white dark:bg-[#333333] text-black dark:text-white'
                          : 'text-[#4b5563] dark:text-[#9ca3af] hover:text-black dark:hover:text-white'
                          }`}
                        onClick={() => setActiveTab('teaching')}
                      >
                        <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 6.25278V19.2528M12 6.25278C10.8321 5.47686 9.24649 5 7.5 5C5.75351 5 4.16789 5.47686 3 6.25278V19.2528C4.16789 18.4769 5.75351 18 7.5 18C9.24649 18 10.8321 18.4769 12 19.2528M12 6.25278C13.1679 5.47686 14.7535 5 16.5 5C18.2465 5 19.8321 5.47686 21 6.25278V19.2528C19.8321 18.4769 18.2465 18 16.5 18C14.7535 18 13.1679 18.4769 12 19.2528" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Created by you
                      </button>
                    )}
                    {tabsToShow.includes('mentoring') && (
                      <button
                        className={`flex items-center justify-center px-1 xxs:px-2 sm:px-4 py-2 rounded-md text-xs sm:text-sm xxs:font-medium cursor-pointer flex-1 sm:flex-initial ${activeTab === 'mentoring'
                          ? 'bg-white dark:bg-[#333333] text-black dark:text-white'
                          : 'text-[#4b5563] dark:text-[#9ca3af] hover:text-black dark:hover:text-white'
                          }`}
                        onClick={() => setActiveTab('mentoring')}
                      >
                        <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Mentored by you
                      </button>
                    )}
                    {tabsToShow.includes('learning') && (
                      <button
                        className={`flex items-center justify-center px-1 xxs:px-2 sm:px-4 py-2 rounded-md text-xs sm:text-sm xxs:font-medium cursor-pointer flex-1 sm:flex-initial ${activeTab === 'learning'
                          ? 'bg-white dark:bg-[#333333] text-black dark:text-white'
                          : 'text-[#4b5563] dark:text-[#9ca3af] hover:text-black dark:hover:text-white'
                          }`}
                        onClick={() => setActiveTab('learning')}
                      >
                        <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Enrolled courses
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Display content based on courses availability */}
              <div className="mb-8">
                {!hasTeachingCourses && !hasMentoringCourses && !hasLearningCourses ? (
                  // No courses at all - show universal placeholder
                  <div className="text-center py-12">
                    <h2 className="text-2xl font-medium mb-2 text-foreground">What if your next big idea became a course?</h2>
                    <p className="text-muted-foreground mb-6">It might be easier than you think</p>
                    <div className="flex justify-center gap-4">
                      <button
                        onClick={handleCreateCourseButtonClick}
                        className="px-6 py-3 text-sm font-medium rounded-full hover:opacity-90 transition-opacity inline-block cursor-pointer bg-foreground text-background"
                      >
                        Create course
                      </button>
                    </div>
                  </div>
                ) : !showSegmentedTabs && (
                  // User has courses but only one role - show appropriate heading
                  <h2 className="text-2xl font-medium text-foreground">
                    {getSingleRoleTitle()}
                  </h2>
                )}
              </div>

              {/* Course grid */}
              {hasAnyCourses && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {getCurrentTabCourses().map((course) => (
                    <CourseCard
                      key={course.id}
                      course={{
                        ...course,
                        title: course.org?.slug ? `@${course.org.slug}/${course.title}` : course.title,
                      }}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {/* Create Course Dialog */}
      <CreateCourseDialog
        open={isCreateCourseDialogOpen}
        onClose={() => setIsCreateCourseDialogOpen(false)}
        onSuccess={handleCourseCreationSuccess}
        schoolId={schoolId || undefined}
      />

      {/* Floating SenseNet Button with transition */}
      {session && (
        <SenseNetButton onClick={() => router.push('/network')} />
      )}
    </>
  );
}


function SenseNetButton({ onClick }: { onClick: () => void }) {
  const [isTransitioning, setIsTransitioning] = useState(false);
  const btnRef = useRef<HTMLButtonElement>(null);

  const playWhooshSound = () => {
    try {
      const ctx = new AudioContext();
      const now = ctx.currentTime;

      // Whoosh — filtered noise sweep
      const bufferSize = ctx.sampleRate * 0.5;
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
      const noise = ctx.createBufferSource();
      noise.buffer = buffer;

      const filter = ctx.createBiquadFilter();
      filter.type = "bandpass";
      filter.frequency.setValueAtTime(200, now);
      filter.frequency.exponentialRampToValueAtTime(4000, now + 0.15);
      filter.frequency.exponentialRampToValueAtTime(600, now + 0.4);
      filter.Q.value = 1.5;

      const noiseGain = ctx.createGain();
      noiseGain.gain.setValueAtTime(0, now);
      noiseGain.gain.linearRampToValueAtTime(0.15, now + 0.05);
      noiseGain.gain.linearRampToValueAtTime(0, now + 0.4);

      noise.connect(filter);
      filter.connect(noiseGain);
      noiseGain.connect(ctx.destination);
      noise.start(now);
      noise.stop(now + 0.5);

      // Chime — two quick tones
      const osc = ctx.createOscillator();
      osc.type = "sine";
      osc.frequency.setValueAtTime(880, now + 0.05);
      osc.frequency.setValueAtTime(1320, now + 0.12);
      const oscGain = ctx.createGain();
      oscGain.gain.setValueAtTime(0, now);
      oscGain.gain.linearRampToValueAtTime(0.2, now + 0.06);
      oscGain.gain.linearRampToValueAtTime(0.15, now + 0.13);
      oscGain.gain.linearRampToValueAtTime(0, now + 0.3);
      osc.connect(oscGain);
      oscGain.connect(ctx.destination);
      osc.start(now + 0.05);
      osc.stop(now + 0.35);
    } catch {}
  };

  const handleClick = () => {
    if (isTransitioning) return;
    playWhooshSound();
    setIsTransitioning(true);
    setTimeout(() => onClick(), 600);
  };

  return (
    <>
      <button
        ref={btnRef}
        onClick={handleClick}
        disabled={isTransitioning}
        aria-label="Open SenseNet"
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-5 py-3 rounded-full shadow-lg bg-black dark:bg-white text-white dark:text-black cursor-pointer transition-all duration-300 hover:scale-110 hover:shadow-2xl active:scale-95 group"
      >
        {/* Pulse ring */}
        <span className="absolute inset-0 rounded-full animate-ping bg-black/20 dark:bg-white/20 opacity-75 group-hover:opacity-0" style={{ animationDuration: "2.5s" }} />

        <Globe className={`w-5 h-5 transition-transform duration-300 ${isTransitioning ? "rotate-180 scale-0" : "group-hover:rotate-12"}`} />
        <span className={`text-sm font-medium hidden sm:inline transition-all duration-300 ${isTransitioning ? "opacity-0 translate-x-2" : ""}`}>
          SenseNet
        </span>
      </button>

      {/* Full-screen transition overlay */}
      {isTransitioning && (
        <div className="fixed inset-0 z-[100] pointer-events-none">
          {/* Expanding circle from bottom-right */}
          <div
            className="absolute rounded-full bg-black dark:bg-white"
            style={{
              bottom: "24px",
              right: "24px",
              width: "60px",
              height: "60px",
              animation: "sensenet-expand 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards",
            }}
          />
          <style>{`
            @keyframes sensenet-expand {
              0% {
                transform: scale(1);
                opacity: 1;
                border-radius: 50%;
              }
              70% {
                transform: scale(50);
                opacity: 1;
                border-radius: 50%;
              }
              100% {
                transform: scale(60);
                opacity: 1;
                border-radius: 0%;
              }
            }
          `}</style>
        </div>
      )}
    </>
  );
}
