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
        arrow.SetActive(false);
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
        x = BitConverter.ToSingle(buffer, 1);
        y = BitConverter.ToSingle(buffer, 5);
        z = BitConverter.ToSingle(buffer, 9);
        if (x == 0 && y == 0 && z == 0)
        {
            arrow.SetActive(false);
            isArrowActive = false;
            return;
        }
        arrow.SetActive(true);
        isArrowActive = true;
        Vector3 arrowVector = new Vector3(x, y, z);
        transform.rotation = Quaternion.LookRotation(arrowVector);
        Quaternion q = Sensor.attitude;
        q.w *= -1;
        transform.rotation = Sensor.attitude;
    }

    void OnGUI()
    {
        if (!isArrowActive)
        {
            GUI.Label(new Rect(0, 50, Screen.width / 2, Screen.height / 2), "현재 위치를 파악할 수 없습니다.\n조금 움직인 후 다시 시도해보세요.");
        }
    }
}


