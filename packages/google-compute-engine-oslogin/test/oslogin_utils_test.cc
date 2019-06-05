// Copyright 2017 Google Inc. All Rights Reserved.
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

// Requires libgtest-dev and gtest compiled and installed.
#include <oslogin_utils.h>

#include <errno.h>
#include <gtest/gtest.h>
#include <stdio.h>
#include <stdlib.h>

using std::string;
using std::vector;

namespace oslogin_utils {

// Test that the buffer can successfully append multiple strings.
TEST(BufferManagerTest, TestAppendString) {
  size_t buflen = 20;
  char* buffer = (char*)malloc(buflen *sizeof(char));
  ASSERT_STRNE(buffer, NULL);

  char* first_string;
  char* second_string;
  int test_errno = 0;
  oslogin_utils::BufferManager buffer_manager(buffer, buflen);
  buffer_manager.AppendString("test1", &first_string, &test_errno);
  buffer_manager.AppendString("test2", &second_string, &test_errno);
  ASSERT_EQ(test_errno, 0);
  ASSERT_STREQ(first_string, "test1");
  ASSERT_STREQ(second_string, "test2");
  ASSERT_STREQ(buffer, "test1");
  ASSERT_STREQ((buffer + 6), "test2");
}

// Test that attempting to append a string larger than the buffer can handle
// fails with ERANGE.
TEST(BufferManagerTest, TestAppendStringTooLarge) {
  size_t buflen = 1;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);

  char* first_string;
  int test_errno = 0;
  oslogin_utils::BufferManager buffer_manager(buffer, buflen);
  ASSERT_FALSE(
      buffer_manager.AppendString("test1", &first_string, &test_errno));
  ASSERT_EQ(test_errno, ERANGE);
}

// Test successfully loading and retrieving an array of JSON posix accounts.
TEST(NssCacheTest, TestLoadJsonArray) {
  NssCache nss_cache(2);
  string test_user1 =
      "{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"uid\":1337,\"gid\":1337,"
      "\"homeDirectory\":\"/home/foo\",\"shell\":\"/bin/bash\"}]}";
  string test_user2 =
      "{\"name\":\"bar@example.com\","
      "\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"bar\",\"uid\":1338,\"gid\":1338,"
      "\"homeDirectory\":\"/home/bar\",\"shell\":\"/bin/bash\"}]}";
  string response = "{\"loginProfiles\": [" + test_user1 + ", " + test_user2 +
                    "], \"nextPageToken\": \"token\"}";

  ASSERT_TRUE(nss_cache.LoadJsonArrayToCache(response));

  size_t buflen = 500;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  struct passwd result;
  int test_errno = 0;

  // Verify that the first user was stored.
  ASSERT_TRUE(nss_cache.HasNextPasswd());
  ASSERT_TRUE(nss_cache.GetNextPasswd(&buf, &result, &test_errno));
  ASSERT_EQ(test_errno, 0);
  ASSERT_EQ(result.pw_uid, 1337);
  ASSERT_EQ(result.pw_gid, 1337);
  ASSERT_STREQ(result.pw_name, "foo");
  ASSERT_STREQ(result.pw_shell, "/bin/bash");
  ASSERT_STREQ(result.pw_dir, "/home/foo");

  // Verify that the second user was stored.
  ASSERT_TRUE(nss_cache.HasNextPasswd());
  ASSERT_TRUE(nss_cache.GetNextPasswd(&buf, &result, &test_errno));
  ASSERT_EQ(test_errno, 0);
  ASSERT_EQ(result.pw_uid, 1338);
  ASSERT_EQ(result.pw_gid, 1338);
  ASSERT_STREQ(result.pw_name, "bar");
  ASSERT_STREQ(result.pw_shell, "/bin/bash");
  ASSERT_STREQ(result.pw_dir, "/home/bar");

  // Verify that there are no more users stored.
  ASSERT_FALSE(nss_cache.HasNextPasswd());
  ASSERT_FALSE(nss_cache.GetNextPasswd(&buf, &result, &test_errno));
  ASSERT_EQ(test_errno, ENOENT);
}

// Test successfully loading and retrieving a partial array.
TEST(NssCacheTest, TestLoadJsonPartialArray) {
  NssCache nss_cache(2);
  string test_user1 =
      "{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"uid\":1337,\"gid\":1337,"
      "\"homeDirectory\":\"/home/foo\",\"shell\":\"/bin/bash\"}]}";
  string response =
      "{\"loginProfiles\": [" + test_user1 + "], \"nextPageToken\": \"token\"}";

  ASSERT_TRUE(nss_cache.LoadJsonArrayToCache(response));

  size_t buflen = 500;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  struct passwd result;
  int test_errno = 0;

  // Verify that the first user was stored.
  ASSERT_TRUE(nss_cache.HasNextPasswd());
  ASSERT_TRUE(nss_cache.GetNextPasswd(&buf, &result, &test_errno));
  ASSERT_EQ(test_errno, 0);
  ASSERT_EQ(result.pw_uid, 1337);
  ASSERT_EQ(result.pw_gid, 1337);
  ASSERT_STREQ(result.pw_name, "foo");
  ASSERT_STREQ(result.pw_shell, "/bin/bash");
  ASSERT_STREQ(result.pw_dir, "/home/foo");

  ASSERT_EQ(nss_cache.GetPageToken(), "token");

  // Verify that there are no more users stored.
  ASSERT_FALSE(nss_cache.HasNextPasswd());
  ASSERT_FALSE(nss_cache.GetNextPasswd(&buf, &result, &test_errno));
  ASSERT_EQ(test_errno, ENOENT);
}

// Test successfully loading and retrieving the final response.
TEST(NssCacheTest, TestLoadJsonFinalResponse) {
  NssCache nss_cache(2);
  string response =
      "{\"nextPageToken\": \"0\"}";

  ASSERT_FALSE(nss_cache.LoadJsonArrayToCache(response));
  ASSERT_EQ(nss_cache.GetPageToken(), "");

  size_t buflen = 500;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  struct passwd result;
  int test_errno = 0;

  // Verify that there are no more users stored.
  ASSERT_FALSE(nss_cache.HasNextPasswd());
  ASSERT_TRUE(nss_cache.OnLastPage());
  ASSERT_FALSE(nss_cache.GetNextPasswd(&buf, &result, &test_errno));
  ASSERT_EQ(test_errno, ENOENT);
}


// Tests that resetting, and checking HasNextPasswd does not crash.
TEST(NssCacheTest, ResetNullPtrTest) {
  NssCache nss_cache(2);
  nss_cache.Reset();
  ASSERT_FALSE(nss_cache.HasNextPasswd());
}

// Test parsing a valid JSON response from the metadata server.
TEST(ParseJsonPasswdTest, ParseJsonToPasswdSucceeds) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"uid\":1337,\"gid\":1338,"
      "\"homeDirectory\":\"/home/foo\",\"shell\":\"/bin/bash\"}]}]}";

  size_t buflen = 200;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  struct passwd result;
  int test_errno = 0;
  ASSERT_TRUE(ParseJsonToPasswd(test_user, &result, &buf, &test_errno));
  ASSERT_EQ(result.pw_uid, 1337);
  ASSERT_EQ(result.pw_gid, 1338);
  ASSERT_STREQ(result.pw_name, "foo");
  ASSERT_STREQ(result.pw_shell, "/bin/bash");
  ASSERT_STREQ(result.pw_dir, "/home/foo");
}

// Test parsing a valid JSON response from the metadata server with uid > 2^31.
TEST(ParseJsonPasswdTest, ParseJsonToPasswdSucceedsWithHighUid) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"uid\":4294967295,\"gid\":"
      "4294967295,\"homeDirectory\":\"/home/foo\",\"shell\":\"/bin/bash\"}]}]}";

  size_t buflen = 200;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  struct passwd result;
  int test_errno = 0;
  ASSERT_TRUE(ParseJsonToPasswd(test_user, &result, &buf, &test_errno));
  ASSERT_EQ(result.pw_uid, 4294967295);
  ASSERT_EQ(result.pw_gid, 4294967295);
  ASSERT_STREQ(result.pw_name, "foo");
  ASSERT_STREQ(result.pw_shell, "/bin/bash");
  ASSERT_STREQ(result.pw_dir, "/home/foo");
}

TEST(ParseJsonPasswdTest, ParseJsonToPasswdSucceedsWithStringUid) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"uid\":\"1337\",\"gid\":"
      "\"1338\",\"homeDirectory\":\"/home/foo\",\"shell\":\"/bin/bash\"}]}]}";

  size_t buflen = 200;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  struct passwd result;
  int test_errno = 0;
  ASSERT_TRUE(ParseJsonToPasswd(test_user, &result, &buf, &test_errno));
  ASSERT_EQ(result.pw_uid, 1337);
  ASSERT_EQ(result.pw_gid, 1338);
  ASSERT_STREQ(result.pw_name, "foo");
  ASSERT_STREQ(result.pw_shell, "/bin/bash");
  ASSERT_STREQ(result.pw_dir, "/home/foo");
}

TEST(ParseJsonPasswdTest, ParseJsonToPasswdNoLoginProfilesSucceeds) {
  string test_user =
      "{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"uid\":1337,\"gid\":1337,"
      "\"homeDirectory\":\"/home/foo\",\"shell\":\"/bin/bash\"}]}";

  size_t buflen = 200;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  struct passwd result;
  int test_errno = 0;
  ASSERT_TRUE(ParseJsonToPasswd(test_user, &result, &buf, &test_errno));
  ASSERT_EQ(result.pw_uid, 1337);
  ASSERT_EQ(result.pw_gid, 1337);
  ASSERT_STREQ(result.pw_name, "foo");
  ASSERT_STREQ(result.pw_shell, "/bin/bash");
  ASSERT_STREQ(result.pw_dir, "/home/foo");
}

// Test parsing a JSON response without enough space in the buffer.
TEST(ParseJsonPasswdTest, ParseJsonToPasswdFailsWithERANGE) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"uid\":1337,\"gid\":1337,"
      "\"homeDirectory\":\"/home/foo\",\"shell\":\"/bin/bash\"}]}]}";

  size_t buflen = 1;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  struct passwd result;
  int test_errno = 0;
  ASSERT_FALSE(ParseJsonToPasswd(test_user, &result, &buf, &test_errno));
  ASSERT_EQ(test_errno, ERANGE);
}

// Test parsing malformed JSON responses.
TEST(ParseJsonPasswdTest, ParseJsonToPasswdFailsWithEINVAL) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"uid\": \"bad_stuff\""
      ",\"gid\":1337,\"homeDirectory\":\"/home/foo\","
      "\"shell\":\"/bin/bash\"}]}]}";
  string test_user2 =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"uid\": 1337,"
      "\"gid\":\"bad_stuff\",\"homeDirectory\":\"/home/foo\","
      "\"shell\":\"/bin/bash\"}]}]}";

  size_t buflen = 200;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  struct passwd result;
  int test_errno = 0;
  ASSERT_FALSE(ParseJsonToPasswd(test_user, &result, &buf, &test_errno));
  ASSERT_EQ(test_errno, EINVAL);
  // Reset errno.
  test_errno = 0;
  ASSERT_TRUE(ParseJsonToPasswd(test_user2, &result, &buf, &test_errno));
  ASSERT_EQ(test_errno, 0);
  ASSERT_EQ(result.pw_uid, 1337);
  ASSERT_EQ(result.pw_gid, 1337);
}

// Test parsing a partially filled response. Validate should fill empty fields
// with default values.
TEST(ParseJsonPasswdTest, ValidatePartialJsonResponse) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"uid\":1337,\"gid\":1337}]"
      "}]}";

  size_t buflen = 200;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  struct passwd result;
  int test_errno = 0;
  ASSERT_TRUE(ParseJsonToPasswd(test_user, &result, &buf, &test_errno));
  ASSERT_EQ(result.pw_uid, 1337);
  ASSERT_EQ(result.pw_gid, 1337);
  ASSERT_STREQ(result.pw_name, "foo");
  ASSERT_STREQ(result.pw_shell, "/bin/bash");
  ASSERT_STREQ(result.pw_dir, "/home/foo");
}

// Test parsing an invalid response. Validate should cause the parse to fail if
// there is no uid.
TEST(ParseJsonPasswdTest, ValidateInvalidJsonResponse) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"gid\":1337}]"
      "}]}";

  size_t buflen = 200;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  struct passwd result;
  int test_errno = 0;
  ASSERT_FALSE(ParseJsonToPasswd(test_user, &result, &buf, &test_errno));
  ASSERT_EQ(test_errno, EINVAL);
}

// Test parsing a valid JSON response from the metadata server.
TEST(ParseJsonToGroupsTest, ParseJsonToGroupsSucceeds) {
  string test_group = 
      "{\"posixGroups\":[{\"name\":\"demo\",\"gid\":123452}]}";

  std::vector<Group> groups;
  ASSERT_TRUE(ParseJsonToGroups(test_group, &groups));
  ASSERT_EQ(groups[0].gid, 123452);
  ASSERT_EQ(groups[0].name, "demo");
}

// Test parsing a valid JSON response from the metadata server with gid > 2^31.
TEST(ParseJsonToGroupsTest, ParseJsonToGroupsSucceedsWithHighGid) {
  string test_group =
      "{\"posixGroups\":[{\"name\":\"demo\",\"gid\":4294967295}]}";

  std::vector<Group> groups;
  ASSERT_TRUE(ParseJsonToGroups(test_group, &groups));
  ASSERT_EQ(groups[0].gid, 4294967295);
  ASSERT_EQ(groups[0].name, "demo");
}

TEST(ParseJsonToGroupsTest, ParseJsonToGroupsSucceedsWithStringGid) {
  string test_group = 
      "{\"posixGroups\":[{\"name\":\"demo\",\"gid\":\"123452\"}]}";

  std::vector<Group> groups;
  ASSERT_TRUE(ParseJsonToGroups(test_group, &groups));
  ASSERT_EQ(groups[0].gid, 123452);
  ASSERT_EQ(groups[0].name, "demo");
}

// Test parsing malformed JSON responses.
TEST(ParseJsonToGroupsTest, ParseJsonToGroupsFails) {
  string test_badgid =
      "{\"posixGroups\":[{\"name\":\"demo\",\"gid\":\"this-should-be-int\"}]}";
  string test_nogid = 
      "{\"posixGroups\":[{\"name\":\"demo\"}]}";
  string test_noname = 
      "{\"posixGroups\":[{\"gid\":123452}]}";

  std::vector<Group> groups;
  ASSERT_FALSE(ParseJsonToGroups(test_badgid, &groups));
  ASSERT_FALSE(ParseJsonToGroups(test_nogid, &groups));
  ASSERT_FALSE(ParseJsonToGroups(test_noname, &groups));
}

// Test parsing a valid JSON response from the metadata server.
TEST(ParseJsonToUsersTest, ParseJsonToUsersSucceeds) {
  string test_group_users = 
      "{\"usernames\":[\"user0001\",\"user0002\",\"user0003\",\"user0004\",\"user0005\"]}";

  std::vector<string> users;
  ASSERT_TRUE(ParseJsonToUsers(test_group_users, &users));
  ASSERT_FALSE(users.empty());
  ASSERT_EQ(users.size(), 5);

  ASSERT_EQ(users[0], "user0001");
  ASSERT_EQ(users[1], "user0002");
  ASSERT_EQ(users[2], "user0003");
  ASSERT_EQ(users[3], "user0004");
  ASSERT_EQ(users[4], "user0005");
}

// Test parsing a valid JSON response from the metadata server.
TEST(ParseJsonToUsersTest, ParseJsonToUsersEmptyGroupSucceeds) {
  string test_group_users = 
      "{\"usernames\":[]}";

  std::vector<string> users;
  ASSERT_TRUE(ParseJsonToUsers(test_group_users, &users));
  ASSERT_TRUE(users.empty());
}

// Test parsing malformed JSON responses.
TEST(ParseJsonToUsersTest, ParseJsonToUsersFails) {
  string test_group_users = 
      "{\"badstuff\":[\"user0001\",\"user0002\",\"user0003\",\"user0004\",\"user0005\"]}";

  std::vector<string> users;
  ASSERT_FALSE(ParseJsonToUsers(test_group_users, &users));
}

TEST(GetUsersForGroupTest, GetUsersForGroupSucceeds) {
  string response;
  long http_code;
  ASSERT_TRUE(HttpGet("http://metadata.google.internal/reset", &response, &http_code));

  std::vector<string> users;
  int errnop = 0;

  ASSERT_TRUE(GetUsersForGroup("demo", &users, &errnop));
  ASSERT_FALSE(users.empty());
  ASSERT_EQ(users[0], "user000173_grande_focustest_org");
  ASSERT_EQ(errnop, 0);
}

TEST(FindGroupTest, FindGroupByGidSucceeds) {
  string response;
  long http_code;
  ASSERT_TRUE(HttpGet("http://metadata.google.internal/reset", &response, &http_code));

  size_t buflen = 200 * sizeof(char);
  char* buffer = (char*)malloc(buflen);
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  int errnop = 0;

  struct group grp = {};
  grp.gr_gid = 123452;
  ASSERT_TRUE(FindGroup(&grp, &buf, &errnop));
  ASSERT_EQ(errnop, 0);
}

TEST(FindGroupTest, FindGroupByNameSucceeds) {
  string response;
  long http_code;
  ASSERT_TRUE(HttpGet("http://metadata.google.internal/reset", &response, &http_code));

  size_t buflen = 200 * sizeof(char);
  char* buffer = (char*)malloc(buflen);
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  int errnop;

  const char* match = "demo";
  struct group grp = {};
  grp.gr_name = (char*)match;
  ASSERT_TRUE(FindGroup(&grp, &buf, &errnop));
}

TEST(ParseJsonEmailTest, SuccessfullyParsesEmail) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"posixAccounts\":["
      "{\"primary\":true,\"username\":\"foo\",\"gid\":1337}]"
      "}]}";

  string email;
  ASSERT_TRUE(ParseJsonToEmail(test_user, &email));
  ASSERT_EQ(email, "foo@example.com");
}

TEST(ParseJsonEmailTest, FailsParseEmail) {
  string email;
  ASSERT_FALSE(ParseJsonToEmail("random_junk", &email));
  ASSERT_EQ(email, "");
}

TEST(ParseJsonSshKeyTest, ParseJsonToSshKeysSucceeds) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"sshPublicKeys\":"
      "{\"fingerprint\": {\"key\": \"test_key\"}}}]}";

  size_t buflen = 200;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  std::vector<string> result = ParseJsonToSshKeys(test_user);
  ASSERT_EQ(result.size(), 1);
  ASSERT_EQ(result[0], "test_key");
}

TEST(ParseJsonSshKeyTest, ParseJsonToSshKeysMultipleKeys) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"sshPublicKeys\":"
      "{\"fingerprint\": {\"key\": \"test_key\"}, \"fingerprint2\": {\"key\": "
      "\"test_key2\"}}}]}";

  size_t buflen = 200;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  std::vector<string> result = ParseJsonToSshKeys(test_user);
  ASSERT_EQ(result.size(), 2);
  ASSERT_EQ(result[0], "test_key");
  ASSERT_EQ(result[1], "test_key2");
}

TEST(ParseJsonSshKeyTest, ParseJsonToSshKeysFiltersExpiredKeys) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"sshPublicKeys\":"
      "{\"fingerprint\": {\"key\": \"test_key\"}, \"fingerprint2\": {\"key\": "
      "\"test_key2\", \"expirationTimeUsec\": 0}}}]}";

  size_t buflen = 200;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  std::vector<string> result = ParseJsonToSshKeys(test_user);
  ASSERT_EQ(result.size(), 1);
  ASSERT_EQ(result[0], "test_key");
}

TEST(ParseJsonSshKeyTest, ParseJsonToSshKeysFiltersMalformedExpiration) {
  string test_user =
      "{\"loginProfiles\":[{\"name\":\"foo@example.com\",\"sshPublicKeys\":"
      "{\"fingerprint\": {\"key\": \"test_key\"}, \"fingerprint2\": {\"key\": "
      "\"test_key2\", \"expirationTimeUsec\": \"bad_stuff\"}}}]}";

  size_t buflen = 200;
  char* buffer = (char*)malloc(buflen * sizeof(char));
  ASSERT_STRNE(buffer, NULL);
  BufferManager buf(buffer, buflen);
  std::vector<string> result = ParseJsonToSshKeys(test_user);
  ASSERT_EQ(result.size(), 1);
  ASSERT_EQ(result[0], "test_key");
}

TEST(ParseJsonAuthorizeSuccess, SuccessfullyAuthorized) {
  string response = "{\"success\": true}";
  ASSERT_TRUE(ParseJsonToSuccess(response));
}

TEST(ValidateUserNameTest, ValidateValidUserNames) {
  string cases[] = {
      "user",
      "_",
      ".",
      ".abc_",
      "_abc-",
      "ABC",
      "A_.-",
      "ausernamethirtytwocharacterslong"
  };
  for (auto test_user : cases) {
    ASSERT_TRUE(ValidateUserName(test_user));
  }
}

TEST(ValidateUserNameTest, ValidateInvalidUserNames) {
  string cases[] = {
      "",
      "!#$%^",
      "-abc",
      "#abc",
      "^abc",
      "abc*xyz",
      "abc xyz",
      "xyz*",
      "xyz$",
      "usernamethirtythreecharacterslong",
      "../../etc/shadow",
  };
  for (auto test_user : cases) {
    ASSERT_FALSE(ValidateUserName(test_user));
  }
}

TEST(ParseJsonKeyTest, TestKey) {
  string test_json = "{\"some_key\":\"some_value\"}";
  string value;
  ASSERT_TRUE(ParseJsonToKey(test_json, "some_key", &value));
  ASSERT_EQ(value, "some_value");
}

TEST(ParseJsonKeyTest, TestMissingKey) {
  string test_json = "{\"some_key\":\"some_value\"}";
  string value;
  ASSERT_FALSE(ParseJsonToKey(test_json, "some_other_key", &value));
  ASSERT_EQ(value, "");
}

TEST(ParseJsonChallengesTest, TestChallenges) {
  string challenges_json = "{\"status\":\"CHALLENGE_REQUIRED\",\"sessionId\":"
      "\"testSessionId\",\"challenges\":[{\"challengeId\":1,\"challengeType\":"
      "\"TOTP\",\"status\":\"READY\"}, {\"challengeId\":2,\"challengeType\":"
      "\"AUTHZEN\",\"status\":\"PROPOSED\"}]}";
  vector<Challenge> challenges;
  ASSERT_TRUE(ParseJsonToChallenges(challenges_json, &challenges));
  ASSERT_EQ(challenges.size(), 2);
  ASSERT_EQ(challenges[0].id, 1);
  ASSERT_EQ(challenges[0].type, "TOTP");
}

TEST(ParseJsonChallengesTest, TestMalformedChallenges) {
  string challenges_json = "{\"status\":\"CHALLENGE_REQUIRED\",\"sessionId\":"
      "\"testSessionId\",\"challenges\":[{\"challengeId\":1,\"challengeType\":"
      "\"TOTP\",\"status\":\"READY\"}, {\"challengeId\":2,\"challengeType\":"
      "\"AUTHZEN\"}]}";
  vector<Challenge> challenges;
  ASSERT_FALSE(ParseJsonToChallenges(challenges_json, &challenges));
  ASSERT_EQ(challenges.size(), 1);
}
}  // namespace oslogin_utils
int main(int argc, char **argv) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
