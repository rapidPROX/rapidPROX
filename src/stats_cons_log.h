/*
// Copyright (c) 2023-2025 rapidPROX contributors
// Copyright (c) 2010-2017 Intel Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
*/

#ifndef _STATS_CONS_LOG_H_
#define _STATS_CONS_LOG_H_

#include "stats_cons.h"

void stats_cons_log_init(void);
void stats_cons_log_notify(void);
void stats_cons_log_finish(void);

struct stats_cons *stats_cons_log_get(void);

#endif /* _STATS_CONS_LOG_H_ */
