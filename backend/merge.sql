
DO $$
DECLARE
  main_id TEXT;
  other_ids TEXT[];
BEGIN
  -- Get first college ID
  SELECT id INTO main_id FROM "College" ORDER BY "createdAt" ASC LIMIT 1;
  
  -- Get other college IDs
  SELECT ARRAY(SELECT id FROM "College" WHERE id != main_id) INTO other_ids;
  
  IF array_length(other_ids, 1) > 0 THEN
    -- Move all data to main college
    UPDATE "User" SET "collegeId" = main_id WHERE "collegeId" = ANY(other_ids);
    UPDATE "ClassSection" SET "collegeId" = main_id WHERE "collegeId" = ANY(other_ids);
    UPDATE "Task" SET "collegeId" = main_id WHERE "collegeId" = ANY(other_ids);
    UPDATE "Material" SET "collegeId" = main_id WHERE "collegeId" = ANY(other_ids);
    UPDATE "Paper" SET "collegeId" = main_id WHERE "collegeId" = ANY(other_ids);
    
    -- Delete other colleges
    DELETE FROM "College" WHERE id = ANY(other_ids);
    
    RAISE NOTICE 'Merged into college: %', main_id;
  ELSE
    RAISE NOTICE 'Only one college exists, no merge needed';
  END IF;
END $$;
