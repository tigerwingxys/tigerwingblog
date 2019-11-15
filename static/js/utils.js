/*
# Copyright 2019 Tigerwing(tigerwingxys@qq.com)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# this file created at 2019.11.14
*/

function checkEmailSyntax(email, aObj) {
    let myReg = /^[a-zA-Z0-9_-]+@([a-zA-Z0-9]+\.)+(\w+)$/;

    if (myReg.test(email)) {
        return true;
    } else {
        aObj.innerText = "邮箱格式不对!";
        return false;
    }
}