I want to create a terminal app called "coalesce" which will basically maintain data about the problems I have solved across all of my codeforces accounts in a json file, and then support various data analysis and visualization features over this data.

# Overwiew:

1. The app should be a global command line tool, that can be accessed from anywhere.
2. The app should maintain a central json file which stores information about all the problems. The columns here will be [Problem Identifier,Problem Link,Rating,Tags,Submission ID,Link to Submission, Submission Time]. 
3. The app should make periodic local backups of this json file.
4. The app should support data analysis features like: display all the problems I have solved with a certain rating, display all the problems i solved within a certain time range, display all the problems I have solved with a certain tag, etc etc. It should be able to output data in the form of simple graphs rendered right inside the terminal. It should also be able to suggest random problems to solve that match certain specified criteria (for example a rating range, whether I have solved said problem before or not, etc.). We will hardcode default values for these criteria in a thoughful manner (for example, by default, we will suggest problems that haven't been solved before).

# Implementation Details:

1. All of the commands will be of the form `coalesce <command and arguments>`. For example `coalesce add <handle>`.
2. Sample code for updating the json file is given in @get_solved.py. However, the given code is for CSV files, I want you to adapt it to JSON files and make this code **overwrite** the existing json file.
3. Specific commands I want for now are:
    1. `coalesce help` - shows a list of all the commands and a short description of what each command does.
    2. `coalesce pull` - refreshes the json file
    3. `coalesce add <handle>` - adds the given handle to the list of alts, and then refreshes the json file to include problems solved by this alt. 
    4. `coalesce remove <handle>` - removes the given handle from the list of alts, and then refreshes the json file to remove problems solved by this alt. 
    5. `coalesce whoami` - shows the list of alts
    6. `coalesce gimme <parameters>` - finds a random problem that matches the given parameters, and then prints <problem identifier> <problem link> (and if the user has used `--spoil`, it will also print <problem rating> <problem tags>). a preliminary list of parameters is given below:
        1. `--spoil` - whether to print the problem rating and tags or not. this will default to false.
        2. `--rating x-y` - restrict the problem rating range to [x, y]. this will default to [0, 3500].
        3. `--tag_and tag1,tag2,...` - return a problem which has ALL of the specified tags. if this is not given, ignore this parameter.
        4. `--tag_or tag1,tag2,...` - return a problem which has AT LEAST ONE of the specified tags. if this is not given, ignore this parameter.
        5. `--solved` - whether to return a problem that has already been solved by the user or not. this will default to false.
    7. `coalesce list <parameters>` - this will list all solved problems (from our central json file) that match the given parameters in the form of a table (rendered within the terminal). A preliminary list of parameters is given below:
        1. `--rating x-y` - restrict the problem rating range to [x, y]. this will default to [0, 3500].
        2. `--tag_and tag1,tag2,...` - restrict to problems which have ALL of the specified tags. if this is not given, ignore this parameter.
        3. `--tag_or tag1,tag2,...` - restrict to problems which have AT LEAST ONE of the specified tags. if this is not given, ignore this parameter.
        4. `--time <time param>` - restrict to problems which were solved within the time range [x, y]. if this is not given, ignore this parameter. input should support -
            1. the form <dd>/<mm>/<yyyy>-<dd>/<mm>/<yyyy> for a date range.
            2. the following natural language phrases - "today", "yesterday", "this week", "this month", "this year", "last week", "last month", "last year"
        5. `--cid <contest id>` - restrict to problems from the given contest. if this is not given, ignore this parameter.
        6. `--pid <problem id>` - restrict to problems from the given problem. if this is not given, ignore this parameter.
8. `coalesce export` - this will export the central 

# CF API Details:

- All codeforces problems can be fetched from: https://codeforces.com/api/problemset.problems. Each problem object has parameters: 

contestId:	Integer. Can be absent. Id of the contest, containing the problem.
problemsetName:	String. Can be absent. Short name of the problemset the problem belongs to.
index:	String. Usually, a letter or letter with digit(s) indicating the problem index in a contest.
name:	String. Localized.
type:	Enum: PROGRAMMING, QUESTION.
points:	Floating point number. Can be absent. Maximum amount of points for the problem.
rating:	Integer. Can be absent. Problem rating (difficulty).
tags:	String list. Problem tags.

- All codeforces submissions of a certain user can be fetched from: https://codeforces.com/api/user.status?handle=<handle>. This use is demonstrated in @get_solved.py, and you can just use code directly from there (after adapting it to JSON of course). Each submission object has parameters:

id	Integer.
contestId	Integer. Can be absent.
creationTimeSeconds	Integer. Time, when submission was created, in unix-format.
relativeTimeSeconds	Integer. Number of seconds, passed after the start of the contest (or a virtual start for virtual parties), before the submission.
problem	Problem object.
author	Party object.
programmingLanguage	String.
verdict	Enum: FAILED, OK, PARTIAL, COMPILATION_ERROR, RUNTIME_ERROR, WRONG_ANSWER, WRONG_ANSWER, TIME_LIMIT_EXCEEDED, MEMORY_LIMIT_EXCEEDED, IDLENESS_LIMIT_EXCEEDED, SECURITY_VIOLATED, CRASHED, INPUT_PREPARATION_CRASHED, CHALLENGED, SKIPPED, TESTING, REJECTED, SUBMITTED. Can be absent.
testset	Enum: SAMPLES, PRETESTS, TESTS, CHALLENGES, TESTS1, ..., TESTS10. Testset used for judging the submission.
passedTestCount	Integer. Number of passed tests.
timeConsumedMillis	Integer. Maximum time in milliseconds, consumed by solution for one test.
memoryConsumedBytes	Integer. Maximum memory in bytes, consumed by solution for one test.
points	Floating point number. Can be absent. Number of scored points for IOI-like contests.
