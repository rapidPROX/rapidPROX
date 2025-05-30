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

#include "bundle.hpp"

void Bundle::toLua(ofstream *f, const string& streamTableName, uint32_t idx) const
{
	(*f) << "bundles[" << idx << "] = {";

	for(vector<uint32_t>::const_iterator i = streams.begin(); i != streams.end(); ++i) {
		(*f) << streamTableName << "[" << (*i) << "]," ;
	}

	(*f) << "}" << endl;
}
