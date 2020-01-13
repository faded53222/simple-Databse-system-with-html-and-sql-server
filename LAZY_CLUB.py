from flask import Flask,url_for,request,render_template,redirect
from datetime import datetime
import pymssql
import socket
default_name='dba'
default_pwd='123456'
database_name='CLUB'
permission={}
class MSSQL:
	def __init__(self,host,user,pwd,db):
		self.host = host
		self.user = user
		self.pwd = pwd
		self.db = db
	def __GetConnect(self):
		if not self.db:
			raise(NameError,"database not found")
		self.conn = pymssql.connect(host=self.host,user=self.user,password=self.pwd,database=self.db,charset="utf8")
		cur = self.conn.cursor()
		if not cur:
			raise(NameError,"fail to connect database")
		else:
			return cur
	def ExecQuery(self,sql):
		cur = self.__GetConnect()
		cur.execute(sql)
		resList = cur.fetchall()
		self.conn.close()
		return resList
	def ExecNonQuery(self,sql):
		cur = self.__GetConnect()
		cur.execute(sql)
		self.conn.commit()
		self.conn.close()
app = Flask(__name__)
def search_info_from_ID(ID):
	A='''
	select * from users
	where uid='{ID}'
	'''.format(ID=ID)
	result=DBA.ExecQuery(A)
	return result[0]
def update_post(text,uid,cid):
	C='''
	insert
	into post
	values('{uid}','{cid}','{content}',0)
	'''.format(uid=uid,cid=cid,content=text)
	DBA.ExecNonQuery(C)
	A='''
	update post
	set count=count+1
	where cid='{cid}'
	'''.format(cid=cid)
	DBA.ExecNonQuery(A)
	B='''
	delete
	from post
	where count>=6
	'''
	DBA.ExecNonQuery(B)
@app.route('/<ID>/my_club', methods=['POST', 'GET'])
def my_club(ID):
	if ID not in permission.keys():
		permission[ID]=0
	if permission[ID]==0:
		return "You don't have permission,try to log in"
	if request.method =='GET':
		return render_template('my_club.html')
	if request.method =='POST':
		if 'sign_club' in request.form.keys():
			return redirect(url_for('sign_up_club',ID=ID))
		if 'Aclub' in request.form.keys():
			return redirect(url_for('club_member',ID=ID))
		if 'Mclub' in request.form.keys():
			return redirect(url_for('manage_club',ID=ID))
		if 'back' in request.form.keys():
			return redirect(url_for('index',ID=ID))
@app.route('/<ID>/search_club', methods=['POST', 'GET'])
def search_club(ID):
	if ID not in permission.keys():
		permission[ID]=0
	if permission[ID]==0:
		return "You don't have permission,try to log in"
	if request.method =='GET':
		return render_template('search_club.html')
	if request.method =='POST':
		if 'search' in request.form.keys():
			CID=request.form['ID']
			name=request.form['name']
			av_list=[]
			in_list=[]
			if CID!="":
				A='''
				select club.cid,cname,discription,users.uname from
				club,user_in_club,users
				where club.cid='{CID}' and user_in_club.cid=club.cid  and user_in_club.uid=users.uid and user_in_club.is_adm=1
				'''.format(CID=CID)
				result=DBA.ExecQuery(A)
				if result is not None:
					av_list+=result
			if name!="":
				A='''
				select club.cid,cname,discription,users.uname from
				club,user_in_club,users
				where cname like '%{name}%' and user_in_club.cid=club.cid  and user_in_club.uid=users.uid and user_in_club.is_adm=1
				'''.format(name=name)
				result=DBA.ExecQuery(A)
				if result is not None:
					av_list+=result
			if CID=='' and name=='':
				A='''
				select club.cid,cname,discription,users.uname from
				club,user_in_club,users
				where user_in_club.cid=club.cid  and user_in_club.uid=users.uid and user_in_club.is_adm=1
				'''
				result=DBA.ExecQuery(A)
				if result is not None:
					av_list=result				
			for each in av_list:
				A='''
				select is_request
				from user_in_club
				where cid={cid} and uid={uid}
				'''.format(cid=each[0],uid=ID)
				result=DBA.ExecQuery(A)
				if result is None or len(result)==0:
					in_list.append('JOIN')
				elif result[0][0]==True:
					in_list.append('CHECKING')
				elif result[0][0]==False:
					in_list.append('JOINED')
			return render_template('search_club.html',av_list=av_list,in_list=in_list)
		if 'back' in request.form.keys():
			return redirect(url_for('index',ID=ID))
		choice_ID=0
		for each in request.form.keys():
			choice_ID=each
		A='''
		insert
		into
		user_in_club
		values('{uid}','{cid}',0,1)
		'''.format(uid=ID,cid=choice_ID)
		DBA.ExecNonQuery(A)
		return render_template('search_club.html')
@app.route('/<ID>/manage_club', methods=['POST', 'GET'])
def manage_club(ID):
	if ID not in permission.keys():
		permission[ID]=0
	if permission[ID]==0:
		return "You don't have permission,try to log in"
	if request.method =='GET':
		av_list=[]
		post_list=[]
		request_list=[]
		club_member_list=[]
		A='''
		select club.cid,cname,discription from
		club,user_in_club,users
		where users.uid={ID} and user_in_club.cid=club.cid  and user_in_club.uid=users.uid and user_in_club.is_adm=1
		'''.format(ID=ID)
		result=DBA.ExecQuery(A)
		if result is not None:
			av_list=result
			for each in result:
				temp=[]
				temp2=[]
				temp3=[]
				B='''
				select content
				from post
				where uid={ID} and cid={cid}
				'''.format(ID=ID,cid=each[0])
				result2=DBA.ExecQuery(B)
				if result2 is not None:
					for each2 in result2:
						temp.append(each2[0])
					post_list.append(temp)
				D='''
				select uname,users.uid
				from
				club,user_in_club,users
				where club.cid={cid} and user_in_club.cid=club.cid  and user_in_club.uid=users.uid and user_in_club.is_request=1
				'''.format(cid=each[0])
				result3=DBA.ExecQuery(D)
				if result3 is not None and len(result3)!=0:
					for each2 in result3:
						temp2.append(each2)
				request_list.append(temp2)
				E='''
				select uname
				from
				club,user_in_club,users
				where club.cid={cid} and user_in_club.cid=club.cid  and user_in_club.uid=users.uid and user_in_club.is_request=0
				'''.format(cid=each[0])
				result4=DBA.ExecQuery(E)
				if result4 is not None and len(result4)!=0:
					for each3 in result4:
						temp3.append(each3)
				club_member_list.append(temp3)
		return render_template('manage_club.html',av_list=av_list,post_list=post_list,request_list=request_list,club_member_list=club_member_list)
	if request.method =='POST':
		if 'back' in request.form.keys():
			return redirect(url_for('my_club',ID=ID))
		choice=''
		for each in request.form.keys():
			choice=each
			print(choice)
			if choice[-1]=='P':
				choice=choice[:-1]
				choice_text=request.form[choice+'PT']
				update_post(choice_text,ID,choice)
			elif choice[-1]=='A' or choice[-1]=='R':
				print(choice)
				print('BB')
				if choice[-1]=='A':
					choice=choice[:-1]
					cl=choice.split('I',1)
					print(cl)
					print('VV')
					A='''
					update user_in_club
					set is_request=0
					where cid='{cid}' and uid='{uid}'
					'''.format(cid=cl[0],uid=cl[1])
					DBA.ExecNonQuery(A)
				if choice[-1]=='R':
					choice=choice[:-1]
					cl=choice.split('I',1)
					A='''
					delete from user_in_club
					where cid='{cid}' and uid='{uid}'
					'''.format(cid=cl[0],uid=cl[1])
					DBA.ExecNonQuery(A)	
		return redirect(url_for('manage_club',ID=ID))
@app.route('/<ID>/club_member', methods=['POST', 'GET'])
def club_member(ID):
	if ID not in permission.keys():
		permission[ID]=0
	if permission[ID]==0:
		return "You don't have permission,try to log in"
	if request.method =='GET':
		av_list=[]
		post_list=[]
		club_member_list=[]
		A='''
		select club.cid,cname,discription from
		club,user_in_club,users
		where users.uid={ID} and user_in_club.cid=club.cid  and user_in_club.uid=users.uid and user_in_club.is_request=0
		'''.format(ID=ID)
		result=DBA.ExecQuery(A)
		if result is not None:
			av_list=result
			for each in result:
				temp=[]
				temp2=[]
				temp3=[]
				B='''
				select content
				from post
				where uid={ID} and cid={cid}
				'''.format(ID=ID,cid=each[0])
				result2=DBA.ExecQuery(B)
				if result2 is not None:
					for each2 in result2:
						temp.append(each2[0])
					post_list.append(temp)
				E='''
				select uname
				from
				club,user_in_club,users
				where club.cid={cid} and user_in_club.cid=club.cid  and user_in_club.uid=users.uid and user_in_club.is_request=0
				'''.format(cid=each[0])
				result4=DBA.ExecQuery(E)
				if result4 is not None and len(result4)!=0:
					for each3 in result4:
						temp3.append(each3)
				club_member_list.append(temp3)
		return render_template('club_member.html',av_list=av_list,post_list=post_list,club_member_list=club_member_list)
	if request.method =='POST':
		if 'back' in request.form.keys():
			return redirect(url_for('my_club',ID=ID))		
@app.route('/<ID>/sign_up_club', methods=['POST', 'GET'])
def sign_up_club(ID):
	if ID not in permission.keys():
		permission[ID]=0
	if permission[ID]==0:
		return "You don't have permission,try to log in"
	if request.method =='GET':
		return render_template('sign_up_club.html')
	if request.method =='POST':
		if 'submit' in request.form.keys():
			message=""
			CID=request.form['ID']
			Cname=request.form['name']
			discription=request.form['discription']
			if CID=="" or Cname=="":
				message="Error: Unfilled blanks"
				return render_template('sign_up_club.html',message=message)
			A='''
			select * from club
			where cid='{ID}' or cname='{name}'
			'''.format(ID=CID,name=Cname)
			result=DBA.ExecQuery(A)
			if len(result)!=0:
				message='Error: Club Already exists'
				return render_template('sign_up_club.html',message=message)
			if message=="":
				A='''
				insert
				into
				club
				values('{cid}','{cname}','{discription}')
				'''.format(cid=CID,cname=Cname,discription=discription)
				DBA.ExecNonQuery(A)
				B='''
				insert
				into
				user_in_club
				values('{uid}','{cid}',1,0)				
				'''.format(uid=ID,cid=CID)
				DBA.ExecNonQuery(B)
				return redirect(url_for('my_club',ID=ID))
		if 'back' in request.form.keys():
			return redirect(url_for('my_club',ID=ID))
@app.route('/<ID>/index',methods=['POST', 'GET'])
def index(ID):
	if ID not in permission.keys():
		permission[ID]=0
	if permission[ID]==0:
		return "You don't have permission,try to log in"
	if request.method =='GET':
		info=search_info_from_ID(ID)
		return render_template('index.html',name=info[1])
	if request.method =='POST':
		if 'VPI' in request.form.keys():
			return redirect(url_for('user_info',ID=ID))
		if 'SC' in request.form.keys():
			return redirect(url_for('search_club',ID=ID))
		if 'MC' in request.form.keys():
			return redirect(url_for('my_club',ID=ID))
		if 'exit' in request.form.keys():
			permission[ID]=0
			return redirect(url_for('login'))
@app.route('/', methods=['POST', 'GET'])
def login():
	if request.method =='GET':
		return render_template('login.html',message="")
	if request.method =='POST':
		if 'login' in request.form.keys():
			ID=request.form['ID']
			password=request.form['password']
			if ID=='' or password=='':
				message=""
			else:
				A='''
				select * from users
				where uid='{ID}' and password='{password}'
				'''.format(ID=ID,password=password)
				result=DBA.ExecQuery(A)
				if len(result)!=0:
					permission[str(ID)]=1
					return redirect(url_for('index',ID=str(ID)))
				A='''
				select * from users
				where uid='{ID}'
				'''.format(ID=ID,password=password)
				result=DBA.ExecQuery(A)
				if len(result)==0:
					message="Error:ID don't exist"
				else:
					message="Error:Wrong password"		
			return render_template('login.html',message=message)
		if 'signup' in request.form.keys():
			return redirect(url_for('signup'))
@app.route('/<ID>/user_info', methods=['POST', 'GET'])
def user_info(ID):
	if ID not in permission.keys():
		permission[ID]=0
	if permission[ID]==0:
		return "You don't have permission,try to log in"
	info=search_info_from_ID(ID)
	if request.method =='GET':
		info=search_info_from_ID(ID)
		return render_template('user_information.html',ID=info[0],name=info[1],college=info[2],grade=info[3],password=info[4])
	if request.method =='POST':
		if 'edit' in request.form.keys():
			return redirect(url_for('user_info_edit',ID=ID))
		if 'back' in request.form.keys():
			return redirect(url_for('index',ID=ID))
@app.route('/<ID>/user_info_edit', methods=['POST', 'GET'])
def user_info_edit(ID):
	if ID not in permission.keys():
		permission[ID]=0
	if permission[ID]==0:
		return "You don't have permission,try to log in"
	info=search_info_from_ID(ID)
	if request.method =='GET':
		return render_template('user_information_edit.html',ID=info[0],_name=info[1],college=info[2],grade=info[3],password=info[4])
	if request.method =='POST':
		if 'submit' in request.form.keys():
			message=""
			name=request.form['name']
			college=request.form['college']
			grade=request.form['grade']
			password1=request.form['password1']
			password2=request.form['password2']
			if name=="" or college=="" or grade=="" or password1=="" or password2=="":
				message="Error: Unfilled blanks"
				return render_template('user_information_edit.html',ID=ID,_name=info[1],college=info[2],grade=info[3],message=message)
			if password1!=password2:
				message='Error: Password dont match'
			if message=="":
				A='''
				update users
				set uname='{uname}',college='{college}',grade='{grade}',password='{password}'
				where uid='{uid}'
				'''.format(uid=ID,uname=name,college=college,grade=grade,password=password1)
				DBA.ExecNonQuery(A)
				return redirect(url_for('user_info',ID=ID))
			else:
				return render_template('user_information_edit.html',ID=ID,_name=info[1],college=info[2],grade=info[3],password=info[4],message=message)
		if 'back' in request.form.keys():
			return redirect(url_for('user_info',ID=ID))
@app.route('/signup', methods=['POST', 'GET'])
def signup():
	if request.method =='GET':
		return render_template('signup.html')
	if request.method =='POST':
		if 'confirmed' in request.form.keys():
			message=""
			ID=request.form['ID']
			name=request.form['name']
			college=request.form['college']
			grade=request.form['grade']
			password1=request.form['password1']
			password2=request.form['password2']
			if ID=="" or name=="" or college=="" or grade=="" or password1=="" or password2=="":
				message="Error: Unfilled blanks"
				return render_template('signup.html',message=message)
			A='''
			select * from users
			where uid='{ID}'
			'''.format(ID=ID)
			result=DBA.ExecQuery(A)
			if len(result)!=0:
				message='Error: User Already exists'
			if password1!=password2:
				message='Error: Password dont match'
			if message=="":
				A='''
				insert
				into
				users
				values('{uid}','{uname}','{college}','{grade}','{password}')
				'''.format(uid=ID,uname=name,college=college,grade=grade,password=password1)
				DBA.ExecNonQuery(A)
				return redirect(url_for('login'))
			else:
				return render_template('signup.html',message=message)
def init():
	global DBA
	global my_IP
	my_IP=socket.gethostbyname(socket.gethostname())
	DBA=MSSQL(my_IP,default_name,default_pwd,database_name)
if __name__ == "__main__":
	init()
	app.run(host=my_IP,debug=True, port=5000)
