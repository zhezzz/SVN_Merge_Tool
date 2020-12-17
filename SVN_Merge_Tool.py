
import shutil
import os
import svn.remote
import svn.local
import sys
from urllib import parse

# 远程仓库
remoteRepositoryUrl = "远程仓库URL"

# 本地源仓库
localSourceRepositoryPath = "本地源仓库"

# 本地目标仓库
localDestRepositoryPath = "本地目标仓库"

# 统一转为Linux下的文件路径分隔符，斜杠“/”
localSourceRepositoryPath = localSourceRepositoryPath.replace(os.sep, "/")
localDestRepositoryPath = localDestRepositoryPath.replace(os.sep, "/")

revisionList = list(map(int, sys.argv[1:]))
revisionList.sort()
addFileList = []
modifyFileList = []
deleteFileList = []
unversioned = "unversioned"
addedOperate = "added"
modifiedOperate = "modified"
deletedOperate = "deleted"
# 映射{文件路径加文件名:操作类型}，例如：{"xx/xx/xx/Item.java": "modified"}
diffDict = {}

remoteClient = svn.remote.RemoteClient(remoteRepositoryUrl)
localClient = svn.local.LocalClient(localDestRepositoryPath)

if len(revisionList) == 0:
	print("请输入SVN版本号")
	exit()

for revision in revisionList:
	try:
		diffList = remoteClient.diff_summary(revision - 1, revision)
		if len(diffList) == 0:
			raise svn.exception.SvnException
	except (svn.exception.SvnException):
		print("远程仓库:", remoteRepositoryUrl, "中, 不存在Revision: ", revision)
		exit()
	for diff in diffList:
		if diff["kind"] != "file":
			continue
		diffPath = parse.unquote(diff["path"].replace(remoteRepositoryUrl, ""))
		diffItem = diff["item"]
		# 添加进dict,判断是否已存在相等的key，不存在则添加，存在则根据已存在元素的value进行判断
		if diffPath not in diffDict:
			diffDict[diffPath] = diffItem
		else:
			# 当dict中已存在added操作的文件，若此时插入deleted操作的同名文件，则从dict中删除此元素；若此时插入modified操作的同名文件，无需修改dict；不存在再次插入added操作的同名文件的情况
			if diffDict[diffPath] == addedOperate:
				if diffItem == deletedOperate:
					diffDict.pop(diffPath)
			# 当dict中已存在modified操作的文件，若此时插入deleted操作的同名文件，则将此文件的操作类型改为deleted；若此时插入modified操作的同名文件，无需修改dict；不存在再次插入added操作的同名文件的情况
			elif diffDict[diffPath] == modifiedOperate:
				if diffItem == deletedOperate:
					diffDict[diffPath] = deletedOperate
			# 当dict中已存在deleted操作的文件，若此时插入added操作的同名文件，则将此文件的操作类型改为modified；不存在插入modified或者deleted操作的同名文件
			elif diffDict[diffPath] == deletedOperate:
				if diffItem == addedOperate:
					diffDict[diffPath] = modifiedOperate

# 写入文件，覆盖文件，删除文件
for key, values in diffDict.items():
	if values == addedOperate:
		(dirPath, fileName) = os.path.split(localSourceRepositoryPath + key)
		dirPath = dirPath.replace(localSourceRepositoryPath, localDestRepositoryPath)
		if not os.path.exists(dirPath):
			os.makedirs(dirPath)
		try:
			shutil.copyfile(localSourceRepositoryPath + key, localDestRepositoryPath + key)
		except FileNotFoundError:
			print("本地源仓库中, 不存在文件: ", localSourceRepositoryPath + key)
			exit()
	if values == modifiedOperate:
		(dirPath, fileName) = os.path.split(localSourceRepositoryPath + key)
		dirPath = dirPath.replace(localSourceRepositoryPath, localDestRepositoryPath)
		if not os.path.exists(dirPath):
			os.makedirs(dirPath)
		try:
			shutil.copyfile(localSourceRepositoryPath + key, localDestRepositoryPath + key)
		except FileNotFoundError:
			print("本地源仓库中, 不存在文件: ", localSourceRepositoryPath + key)
			exit()
	if values == deletedOperate:
		if os.path.exists(localDestRepositoryPath + key):
			os.remove(localDestRepositoryPath + key)

# 打印操作的文件
print("*" * 150)
print(revisionList, ", Revision数量:", len(revisionList), ", 影响的文件数量:", len(diffDict))
print("*" * 60)
for key, value in diffDict.items():
	print(key + "-----" + value)
print("*" * 150)

# 打印本地目标仓库文件变更详情
# tmp = localClient.status()
for status in localClient.status():
	statusName = str(status.name).encode("GBK").decode("UTF-8")
	# 如果本地目标仓库中发生变更的文件不在远程源仓库的变更列表中，则跳过,（暂不实现）
	# if  status.name.replace(os.sep, "/").replace(localDestRepositoryPath, "") not in diffDict:
	#     continue
	if status.type_raw_name == unversioned:
		# localClient.add(status.name.replace(os.sep, "/").replace(localDestRepositoryPath, "./"))
		addFileList.append(statusName)
	if status.type_raw_name == addedOperate:
		addFileList.append(statusName)
	if status.type_raw_name == modifiedOperate:
		modifyFileList.append(statusName)
	if status.type_raw_name == deletedOperate:
		deleteFileList.append(statusName)
print("本地目标仓库文件变更情况：")
print("*" * 30)
print("新增(", len(addFileList), ")：")
for item in addFileList:
	print(item.replace(os.sep, "/").replace(localDestRepositoryPath, ""))
print("修改(", len(modifyFileList), ")：")
for item in modifyFileList:
	print(item.replace(os.sep, "/").replace(localDestRepositoryPath, ""))
print("删除(", len(deleteFileList), ")：")
for item in deleteFileList:
	print(item.replace(os.sep, "/").replace(localDestRepositoryPath, ""))
