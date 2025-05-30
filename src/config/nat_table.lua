--
-- Copyright (c) 2023-2025 rapidPROX contributors
-- Copyright (c) 2010-2017 Intel Corporation
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--

return {
   {from = ip("10.10.100.100"), to = ip("192.168.1.1")},
   {from = ip("192.168.1.1"), to = ip("10.10.100.100")},
   {from = ip("192.168.1.101"), to = ip("10.10.10.101")},
   {from = ip("10.10.10.101"), to = ip("192.168.1.101")},
   {from = ip("192.168.1.102"), to = ip("10.10.10.102")},
   {from = ip("10.10.10.102"), to = ip("192.168.1.102")},
   {from = ip("192.168.100.100"), to = ip("10.0.100.100")},
   {from = ip("10.0.100.100"), to = ip("192.168.100.100")},
}
