using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using System;
using System.Text;
using System.Net.Sockets;

public class Arrow : MonoBehaviour
{
    private GameObject arrow;
    Socket data_sock = Loading.Instance.GetDatatSocket();
    byte[] buffer = new byte[1024];
    bool isArrowActive = true;
    // Start is called before the first frame update
    void Start()
    {
        arrow = GameObject.Find("Arrow");
    }

    // Update is called once per frame
    void Update()
    {
        if (!Destination.Instance.GetIsInputFilled())  //목적지 입력 안됨
        {
            return;
        }
        data_sock.Receive(buffer, 1024, SocketFlags.None);
        float x, y, z;
        z = -BitConverter.ToSingle(buffer, 1);
        y = BitConverter.ToSingle(buffer, 5);
        x = BitConverter.ToSingle(buffer, 9);
        Debug.Log(x);
        Debug.Log(y);
        Debug.Log(z);
        if (x == 0 && y == 0 && z == 0)
        {
            isArrowActive = false;
            return;
        }
        Debug.Log("asd");
        isArrowActive = true;
        Vector3 arrowVector = new Vector3(x, y, z);
        transform.rotation = Quaternion.LookRotation(arrowVector);
        Quaternion q = Quaternion.Inverse(Sensor.attitude);
        Quaternion q2 = q;
        q.x = q2.z;
        q.z = -q2.x;
        transform.rotation = q * transform.rotation;
    }

    void OnGUI()
    {
        if (!isArrowActive)
        {
            GUI.Label(new Rect(0, 50, Screen.width / 2, Screen.height / 2), "현재 위치를 파악할 수 없습니다.\n조금 움직인 후 다시 시도해보세요.");
        }
    }
}


