/**
 * Calculates the status of each subject based on completed subjects and prerequisites.
 * 
 * @param {Array} subjects - Full list of subjects
 * @param {Array} completedIds - List of IDs or Codes of courses completed by the student
 * @returns {Object} A map associating the subject ID with its status ('completed' | 'available' | 'blocked')
 */
export function calculateSubjectStatuses(subjects, completedIds = []) {
  // Standardize completed IDs for fast, case-insensitive lookup
  const completedSet = new Set(completedIds.map(id => String(id).trim().toLowerCase()));
  const statuses = {};

  // First step: initialize
  subjects.forEach(subject => {
    const subjectId = String(subject.id).trim().toLowerCase();
    const subjectCode = String(subject.code).trim().toLowerCase();

    // A subject is considered completed if its ID or Code is in the completed list
    if (completedSet.has(subjectId) || completedSet.has(subjectCode)) {
      statuses[subject.id] = 'completed';
    }
  });

  // Second step: determine status for non-completed subjects
  subjects.forEach(subject => {
    if (statuses[subject.id] === 'completed') {
      return;
    }

    const prereqs = subject.prerequisites || [];

    if (prereqs.length === 0) {
      // No prerequisites: available for enrollment
      statuses[subject.id] = 'available';
    } else {
      // Verify if all prerequisites are completed
      const allMet = prereqs.every(prereqId => {
        const pId = String(prereqId).trim().toLowerCase();
        
        // If the prerequisite is not part of the student's curriculum, ignore it
        const isPartofCurriculum = subjects.some(s => 
          String(s.id).trim().toLowerCase() === pId || 
          String(s.code).trim().toLowerCase() === pId
        );
        if (!isPartofCurriculum) {
          return true; // Ignore prerequisite that is not part of the curriculum
        }
        
        // Check if the prerequisite course is completed
        // First, check if the prereqId itself was marked as completed in our statuses map
        if (statuses[prereqId] === 'completed') {
          return true;
        }

        // Or if the prereqId is in the completed Set
        if (completedSet.has(pId)) {
          return true;
        }

        // Also check if prereqId is a course code and if any course with that code is completed
        const matchingSubject = subjects.find(s => 
          String(s.id).trim().toLowerCase() === pId || 
          String(s.code).trim().toLowerCase() === pId
        );
        
        if (matchingSubject && statuses[matchingSubject.id] === 'completed') {
          return true;
        }

        return false;
      });

      statuses[subject.id] = allMet ? 'available' : 'blocked';
    }
  });

  return statuses;
}
