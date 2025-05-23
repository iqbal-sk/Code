/**
 * This file was auto-generated by openapi-typescript.
 * Do not make direct changes to the file.
 */

export interface paths {
    "/api/v1/users/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Register */
        post: operations["register_api_v1_users_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/users/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_api_v1_users_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/problems/{problem_id}/test-cases": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Test Cases */
        get: operations["list_test_cases_api_v1_problems__problem_id__test_cases_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/problems/{problem_id}/test-cases/public": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Public Test Cases */
        get: operations["list_public_test_cases_api_v1_problems__problem_id__test_cases_public_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/submissions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Enqueue a new code submission */
        post: operations["create_submission_api_v1_submissions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/submissions/{submission_id}/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Stream live status updates for a submission */
        get: operations["submission_events_api_v1_submissions__submission_id__events_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/submissions/problems/{problem_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List your submissions for a specific problem (paginated) */
        get: operations["list_my_submissions_for_problem_api_v1_submissions_problems__problem_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/problems/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Read Problems
         * @description List problems with optional filters and pagination.
         */
        get: operations["read_problems_api_v1_problems__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/problems/{problem_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Read Problem
         * @description Retrieve a single problem by its ID.
         */
        get: operations["read_problem_api_v1_problems__problem_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AllTestCasesResponse */
        AllTestCasesResponse: {
            /** Testcases */
            testCases: components["schemas"]["TestCase"][];
        };
        /** ConstraintsResponse */
        ConstraintsResponse: {
            /** Timelimit Ms */
            timeLimit_ms: number;
            /** Memorylimit Mb */
            memoryLimit_mb: number;
            /** Inputformat */
            inputFormat: string;
            /** Outputformat */
            outputFormat: string;
            /** Pconstraints */
            pConstraints: string[];
        };
        /** DescriptionResponse */
        DescriptionResponse: {
            /** Markdown */
            markdown: string;
            /** Html */
            html: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** Preferences */
        Preferences: {
            /**
             * Theme
             * @default light
             */
            theme: string | null;
            /**
             * Editorsettings
             * @default {}
             */
            editorSettings: {
                [key: string]: unknown;
            } | null;
            /**
             * Notifications
             * @default true
             */
            notifications: boolean | null;
        };
        /**
         * ProblemDetailResponse
         * @description Full detail view for a single problem.
         */
        ProblemDetailResponse: {
            /** Pid */
            pId: number;
            /** Title */
            title: string;
            /** Slug */
            slug: string;
            /** Difficulty */
            difficulty: string | null;
            /** Tags */
            tags: string[] | null;
            /** Acceptancerate */
            acceptanceRate?: number | null;
            description: components["schemas"]["DescriptionResponse"];
            constraints: components["schemas"]["ConstraintsResponse"];
            /** Sampletestcases */
            sampleTestCases: components["schemas"]["SampleTestCaseResponse"][];
            statistics: components["schemas"]["StatisticsResponse"];
            /** Assets */
            assets: string[] | null;
            /** Visibility */
            visibility: string;
        };
        /** ProblemListResponse */
        ProblemListResponse: {
            /** Total */
            total: number;
            /** Page */
            page: number;
            /** Page Size */
            page_size: number;
            /** Items */
            items: components["schemas"]["ProblemSummaryResponse"][];
        };
        /**
         * ProblemSummaryResponse
         * @description Lightweight view for listing problems.
         */
        ProblemSummaryResponse: {
            /** Pid */
            pId: number;
            /** Title */
            title: string;
            /** Slug */
            slug: string;
            /** Difficulty */
            difficulty: string | null;
            /** Tags */
            tags: string[] | null;
            /** Acceptancerate */
            acceptanceRate?: number | null;
        };
        /** PublicTestCase */
        PublicTestCase: {
            /** Caseid */
            caseId: string;
            /** Isremote */
            isRemote: boolean;
            /** Inputpath */
            inputPath?: string | null;
            /** Outputpath */
            outputPath?: string | null;
        };
        /** PublicTestCasesResponse */
        PublicTestCasesResponse: {
            /** Testcases */
            testCases: components["schemas"]["PublicTestCase"][];
        };
        /** SampleTestCaseResponse */
        SampleTestCaseResponse: {
            /** Input */
            input: string;
            /** Expectedoutput */
            expectedOutput: string;
            /** Explanation */
            explanation: string;
        };
        /** SocialLinks */
        SocialLinks: {
            /** Github */
            github?: string | null;
            /** Linkedin */
            linkedin?: string | null;
            /** Twitter */
            twitter?: string | null;
        };
        /** StatisticsResponse */
        StatisticsResponse: {
            /** Submissions */
            submissions: number;
            /** Accepted */
            accepted: number;
        };
        /** Stats */
        Stats: {
            /**
             * Problemssolved
             * @default 0
             */
            problemsSolved: number | null;
            /**
             * Totalsubmissions
             * @default 0
             */
            totalSubmissions: number | null;
            /**
             * Successfulsubmissions
             * @default 0
             */
            successfulSubmissions: number | null;
            /** Rank */
            rank?: number | null;
        };
        /** SubmissionCreate */
        SubmissionCreate: {
            /**
             * Problemid
             * @description MongoDB ObjectId as hex string
             */
            problemId: string;
            /** Language */
            language: string;
            /** Sourcecode */
            sourceCode: string;
            /**
             * Stdin
             * @default
             */
            stdin: string | null;
        };
        /** SubmissionResponse */
        SubmissionResponse: {
            /** Id */
            id: string;
            /** Userid */
            userId: string;
            /** Problemid */
            problemId: string;
            /** Language */
            language: string;
            /** Sourcecode */
            sourceCode: string;
            /** Stdin */
            stdin: string | null;
            /** Status */
            status: string;
            /**
             * Submittedat
             * Format: date-time
             */
            submittedAt: string;
            /** Completedat */
            completedAt: string | null;
            result: components["schemas"]["SubmissionResult"] | null;
            /** Canceled */
            canceled: boolean;
            /**
             * Createdat
             * Format: date-time
             */
            createdAt: string;
            /**
             * Updatedat
             * Format: date-time
             */
            updatedAt: string;
        };
        /** SubmissionResponseList */
        SubmissionResponseList: {
            /** Submissions */
            submissions: components["schemas"]["SubmissionResponse"][];
            /** Total */
            total: number;
            /** Page */
            page: number;
            /** Limit */
            limit: number;
        };
        /** SubmissionResult */
        SubmissionResult: {
            /** Totaltests */
            totalTests: number;
            /** Passedtests */
            passedTests: number;
            /** Max Runtime Ms */
            max_runtime_ms: number;
            /** Max Memory Bytes */
            max_memory_bytes: number;
            /** Testdetails */
            testDetails: components["schemas"]["TestDetail"][];
        };
        /** TestCase */
        TestCase: {
            /** Caseid */
            caseId: string;
            /** Isremote */
            isRemote: boolean;
            /** Ishidden */
            isHidden: boolean;
            /** Inputpath */
            inputPath?: string | null;
            /** Outputpath */
            outputPath?: string | null;
            /** Input */
            input?: string | null;
            /** Expectedoutput */
            expectedOutput?: string | null;
        };
        /** TestDetail */
        TestDetail: {
            /** Testcaseid */
            testCaseId: string;
            /** Verdict */
            verdict: string;
            /** Status */
            status: string;
            /** Stdout */
            stdout: string;
            /** Runtime Ms */
            runtime_ms: number;
            /** Memory Bytes */
            memory_bytes: number;
            /** Errormessage */
            errorMessage?: string | null;
        };
        /** Token */
        Token: {
            /** Access Token */
            access_token: string;
            /** Token Type */
            token_type: string;
        };
        /** UserCreate */
        UserCreate: {
            /** Username */
            username: string;
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Firstname */
            firstName: string;
            /** Lastname */
            lastName: string;
            /** Role */
            role?: string[] | null;
            /** Profilepicture */
            profilePicture?: string | null;
            /** Bio */
            bio?: string | null;
            socialLinks?: components["schemas"]["SocialLinks"] | null;
            preferences?: components["schemas"]["Preferences"] | null;
            /** Password */
            password: string;
        };
        /** UserLogin */
        UserLogin: {
            /** Username */
            username: string;
            /** Password */
            password: string;
        };
        /** UserOut */
        UserOut: {
            /** Username */
            username: string;
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Firstname */
            firstName: string;
            /** Lastname */
            lastName: string;
            /** Role */
            role?: string[] | null;
            /** Profilepicture */
            profilePicture?: string | null;
            /** Bio */
            bio?: string | null;
            socialLinks?: components["schemas"]["SocialLinks"] | null;
            preferences?: components["schemas"]["Preferences"] | null;
            /** Id */
            _id: string;
            stats?: components["schemas"]["Stats"] | null;
            /** Createdat */
            createdAt?: string | null;
            /** Updatedat */
            updatedAt?: string | null;
            /** Lastlogin */
            lastLogin?: string | null;
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    register_api_v1_users_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UserCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    login_api_v1_users_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UserLogin"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Token"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_test_cases_api_v1_problems__problem_id__test_cases_get: {
        parameters: {
            query?: {
                includeHidden?: boolean;
            };
            header?: never;
            path: {
                problem_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AllTestCasesResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_public_test_cases_api_v1_problems__problem_id__test_cases_public_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                problem_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PublicTestCasesResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_submission_api_v1_submissions_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SubmissionCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submission_events_api_v1_submissions__submission_id__events_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                submission_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_my_submissions_for_problem_api_v1_submissions_problems__problem_id__get: {
        parameters: {
            query?: {
                /** @description Page number, starting from 1 */
                page?: number;
                /** @description Items per page */
                limit?: number;
            };
            header?: never;
            path: {
                problem_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionResponseList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_problems_api_v1_problems__get: {
        parameters: {
            query?: {
                /** @description Page number, starting from 1 */
                page?: number;
                /** @description Items per page */
                page_size?: number;
                /** @description Filter by difficulty level */
                difficulty?: string | null;
                /** @description Filter by tag(s) */
                tags?: string[] | null;
                /** @description Text search on title and description */
                text?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProblemListResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_problem_api_v1_problems__problem_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                problem_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProblemDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
